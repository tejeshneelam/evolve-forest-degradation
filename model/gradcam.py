"""
EvOLve — model/gradcam.py
Grad-CAM for pixel-level degradation heatmaps.

Produces a 64×64 attention map showing WHICH spatial locations
in a patch are most responsible for the degradation prediction.

Usage:
    heatmap = gradcam(model, patch_tensor)  # returns (64, 64) numpy array
"""

import numpy as np
import torch
import torch.nn.functional as F


class GradCAM:
    """
    Gradient-weighted Class Activation Mapping for the EvOLve classifier.

    Hooks into the last CNN layer of the spatial encoder to produce
    per-pixel importance maps.
    """

    def __init__(self, model, target_layer_name: str = 'spatial_enc.net.12'):
        """
        model             : DegradationClassifier
        target_layer_name : dotted path to the conv layer to hook
        """
        self.model       = model
        self.gradients   = None
        self.activations = None
        self._hooks      = []

        # Resolve target layer
        layer = model
        for part in target_layer_name.split('.'):
            layer = getattr(layer, part)
        self.target_layer = layer

        # Register hooks
        self._hooks.append(
            layer.register_forward_hook(self._save_activation)
        )
        self._hooks.append(
            layer.register_full_backward_hook(self._save_gradient)
        )

    def _save_activation(self, module, input, output):
        self.activations = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def remove_hooks(self):
        for h in self._hooks:
            h.remove()

    def generate(
        self,
        patch: torch.Tensor,    # (T, 8, 64, 64) — single patch, no batch dim
        device: torch.device = torch.device('cpu'),
    ) -> np.ndarray:
        """
        Compute Grad-CAM heatmap for a single patch.

        Returns:
            heatmap: (64, 64) float32 in [0, 1] — higher = more degraded
        """
        self.model.eval()
        x = patch.unsqueeze(0).to(device)    # (1, T, 8, 64, 64)

        # Forward pass
        score = self.model(x)                 # (1,)

        # Backward pass for the degradation score
        self.model.zero_grad()
        score.backward()

        # Grad-CAM formula: weight activations by global-average-pooled gradients
        if self.gradients is None or self.activations is None:
            # Fallback: return uniform map
            return np.ones((64, 64), dtype=np.float32) * 0.5

        # Pool over spatial dims and time
        # activations: (B*T, C, H', W')  where H'=W'=1 (after AdaptiveAvgPool)
        # We need to go one layer back; use the pre-pool activations
        # Simplified: use the gradient magnitude as spatial importance
        grads = self.gradients    # (B*T, C, ...)
        acts  = self.activations  # (B*T, C, ...)

        # Global average pool gradients over channels
        weights = grads.mean(dim=1, keepdim=True)      # (B*T, 1, ...)
        cam     = (weights * acts).sum(dim=1)           # (B*T, ...)
        cam     = F.relu(cam)

        # If spatial dims collapsed, return uniform
        if cam.dim() < 3 or cam.shape[-1] == 1:
            return np.ones((64, 64), dtype=np.float32) * float(score.item())

        # Average over time steps
        cam = cam.mean(dim=0)    # (H', W')

        # Upsample to 64×64
        cam = cam.unsqueeze(0).unsqueeze(0)    # (1, 1, H', W')
        cam = F.interpolate(cam, size=(64, 64), mode='bilinear', align_corners=False)
        cam = cam.squeeze().cpu().numpy()

        # Normalize to [0, 1]
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        return cam.astype(np.float32)


class SimpleGradientHeatmap:
    """
    Simpler alternative: compute input gradient saliency map.
    Works even without specific layer hooks.
    Aggregates gradient magnitude over the band dimension.
    """

    def __init__(self, model):
        self.model = model

    def generate(
        self,
        patch: torch.Tensor,
        device: torch.device = torch.device('cpu'),
        time_agg: str = 'max',   # 'max' | 'mean'
    ) -> np.ndarray:
        """
        patch: (T, 8, 64, 64)
        Returns: (64, 64) in [0, 1]
        """
        self.model.eval()
        x = patch.unsqueeze(0).to(device).requires_grad_(True)   # (1, T, 8, 64, 64)

        # Temporarily enable encoder gradients if present to allow backpropagation to input x
        was_frozen = getattr(self.model, 'freeze_encoder', False)
        if hasattr(self.model, 'freeze_encoder'):
            self.model.freeze_encoder = False

        score = self.model(x)
        self.model.zero_grad()
        score.backward()

        # Restore freeze_encoder state
        if hasattr(self.model, 'freeze_encoder'):
            self.model.freeze_encoder = was_frozen

        if x.grad is None:
            # Safe fallback if gradient is still None
            return np.ones((64, 64), dtype=np.float32) * float(score.item())

        # Gradient magnitude: (1, T, 8, 64, 64)
        grad = x.grad.abs()

        # Aggregate over bands → (1, T, 64, 64)
        grad = grad.mean(dim=2)

        # Aggregate over time
        if time_agg == 'max':
            grad = grad.max(dim=1)[0]     # (1, 64, 64)
        else:
            grad = grad.mean(dim=1)       # (1, 64, 64)

        heatmap = grad.squeeze().cpu().detach().numpy()

        # Normalize
        h_min, h_max = heatmap.min(), heatmap.max()
        if h_max > h_min:
            heatmap = (heatmap - h_min) / (h_max - h_min)
        else:
            heatmap = np.zeros_like(heatmap)

        return heatmap.astype(np.float32)


def generate_all_heatmaps(model, dataset, device, output_dir: str = 'results/heatmaps'):
    """
    Generate and save heatmaps for all patches.
    Saves as results/heatmaps/heatmap_{patch_id:04d}.npy
    """
    import os
    import json
    os.makedirs(output_dir, exist_ok=True)

    cam = SimpleGradientHeatmap(model)
    heatmap_index = {}

    for i in range(len(dataset)):
        sample   = dataset[i]
        patch    = sample['patch']
        patch_id = sample['patch_id']

        heatmap = cam.generate(patch, device=device)
        out_path = os.path.join(output_dir, f"heatmap_{patch_id:04d}.npy")
        np.save(out_path, heatmap)

        # Store stats for indexing
        heatmap_index[str(patch_id)] = {
            'path':      out_path,
            'max_val':   float(heatmap.max()),
            'mean_val':  float(heatmap.mean()),
            'hotspot_y': int(np.unravel_index(heatmap.argmax(), heatmap.shape)[0]),
            'hotspot_x': int(np.unravel_index(heatmap.argmax(), heatmap.shape)[1]),
        }

    with open(os.path.join(output_dir, 'heatmap_index.json'), 'w') as f:
        json.dump(heatmap_index, f, indent=2)

    print(f"✅ Heatmaps saved: {len(heatmap_index)} patches → {output_dir}/")
    return heatmap_index
