"""Frozen scoring of the supplied model-ready AIF arrays."""
from pathlib import Path
import hashlib
import numpy as np
import torch
from torch import nn
from torchvision.models import resnet50


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


class FeatureHead(nn.Module):
    def __init__(self,state):
        super().__init__()
        first=state['fc.fc1.weight'];second=state['fc.fc2.weight']
        self.fc1=nn.Linear(first.shape[1],first.shape[0])
        self.fc2=nn.Linear(second.shape[1],second.shape[0])
    def forward(self,x):
        return torch.relu(self.fc2(torch.relu(self.fc1(x))))


def load_scorer(path,expected_hash,device):
    if sha256(path)!=expected_hash:raise ValueError('Model checksum mismatch')
    payload=torch.load(path,map_location='cpu',weights_only=True)
    if set(payload)!={'encoder','score_weight','score_bias'}:raise ValueError('Unexpected inference artifact')
    model=resnet50(weights=None);model.fc=FeatureHead(payload['encoder'])
    model.load_state_dict(payload['encoder'],strict=True)
    return model.to(device).eval(),payload['score_weight'].numpy(),float(payload['score_bias'])


@torch.inference_mode()
def score_paths(paths,model,weight,bias,device):
    scores=[]
    for path in paths:
        image=np.load(path,allow_pickle=False)
        if image.ndim!=2 or image.dtype!=np.float32 or not np.isfinite(image).all():
            raise ValueError('Expected supplied2D float32 model-ready AIF array')
        if image.min()<0 or image.max()>1:raise ValueError('Model-ready AIF values must be in [0,1]')
        x=torch.from_numpy(np.ascontiguousarray(np.repeat(image[None],3,axis=0)))[None].to(device)
        features=model(x).cpu().numpy()[0].astype(np.float64)
        scores.append(float(features@weight+bias))
    return np.asarray(scores)
