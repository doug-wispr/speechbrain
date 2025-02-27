"""This lobe enables the integration of huggingface pretrained wav2vec2 models.

Reference: https://arxiv.org/abs/2006.11477
Reference: https://arxiv.org/abs/1904.05862
Reference: https://arxiv.org/abs/2110.13900
Transformer from HuggingFace needs to be installed:
https://huggingface.co/transformers/installation.html

Authors
 * Salah Zaiem 2023
 * Adel Moumen 2023, 2024
"""

import torch
import logging
import torch.nn.functional as F
from speechbrain_experimental.lobes.models.huggingface_transformers.huggingface import (
    HFTransformersInterface,
)

logger = logging.getLogger(__name__)


class WeightedSSLModel(HFTransformersInterface):
    """This lobe enables the integration of use of weighted sum representations
    from different layers in a SSL encoder.

    The model can be used as a fixed feature extractor for SSL benchmarking. It
    will download automatically the model from HuggingFace or use a local path.

    More details in recipes/SSL_benchmark

    Arguments
    ---------
    hub : str
        HuggingFace hub name: e.g "facebook/wav2vec2-large-lv60"
    save_path : str
        Path (dir) of the downloaded model.
    layernorm: bool, (default: False)
        Whether layer representations should be layernormed before sum
    freeze : bool (default: True)
        If True, the model is frozen. If False, the model will be trained
        alongside with the rest of the pipeline.

    Example
    -------
    >>> inputs = torch.rand([10, 600])
    >>> model_hub = "facebook/wav2vec2-base-960h"
    >>> save_path = "savedir"
    >>> model = WeightedSSLModel(model_hub, save_path)
    >>> outputs = model(inputs)
    """

    def __init__(self, hub, save_path="", layernorm=False, freeze=False):
        super().__init__(source=hub, save_path=save_path, freeze=freeze)
        self.model.eval()
        self.num_layers = self.config.num_hidden_layers + 1
        # Initializing the learnable weights
        zero_init = torch.cat([torch.zeros(self.num_layers)])
        self.weights = torch.nn.Parameter(zero_init, requires_grad=True)
        self.layernorm = layernorm

    def forward(self, wav, wav_lens=None):
        """This method outputs a weighted sum of the layers representations of the SSL encoder

        Arguments
        ---------
        wav : tensor
            The wavs
        wav_lens : tensor
            The wav lengths
        """

        feats = self.model(wav)
        hidden_states = torch.stack(feats.hidden_states, dim=0).detach()
        # First dimension should be equal to the number of layers in the hparams
        assert (
            self.num_layers == hidden_states.shape[0]
        ), "Num layers not equal to num hidden states"
        norm_weights = torch.nn.functional.softmax(self.weights, dim=-1)
        # Layernorming the layers representations if asked
        if self.layernorm:
            hidden_states = [
                F.layer_norm(t, (t.shape[-1],)) for t in hidden_states
            ]
        # Summing the weighted layers
        weighted_feats = (
            hidden_states * norm_weights[:, None, None, None]
        ).sum(axis=0)
        return weighted_feats

    def override_config(self, config):
        """If the config needs to be overrided, here is the place

        Arguments
        ---------
        config : Wav2Vec2Config
            The original config needs to be overrided.

        Returns
        -------
        Overridded config
        """
        config.output_hidden_states = True
        return config
