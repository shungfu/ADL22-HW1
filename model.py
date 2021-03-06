from typing import Dict

import torch
import torch.nn as nn


class SeqClassifier(torch.nn.Module):
    def __init__(
        self,
        embeddings: torch.tensor,
        hidden_size: int,
        num_layers: int,
        dropout: float,
        bidirectional: bool,
        num_class: int,
        sequence_length: int,
    ) -> None:
        super(SeqClassifier, self).__init__()
        self.embed = nn.Embedding.from_pretrained(embeddings, freeze=False)
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.seq_len = sequence_length
        self.D = 2 if bidirectional else 1

        input_size = embeddings.shape[1]

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True,
                            dropout=dropout, bidirectional=bidirectional)

        # self.fc = nn.Linear(hidden_size*self.D, num_class)
        self.fc = nn.Sequential(
            nn.Linear(self.encoder_output_size, hidden_size),
            nn.BatchNorm1d(hidden_size),
            # nn.ReLU(),
            nn.LeakyReLU(0.2),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_class)
        )
        self.ln = nn.LayerNorm(input_size)

    def forward(self, batch) -> torch.Tensor:

        embed_batch = self.embed(batch)
        embed_batch = self.ln(embed_batch)

        output, (h_n, c_n) = self.lstm(embed_batch)
        # out = self.fc(output[:,-1,:]) # the last hidde state
        out = self.fc(output.contiguous().view(output.shape[0], -1))

        return out

    @property
    def encoder_output_size(self) -> int:
        return self.hidden_size * self.D * self.seq_len


class SlottTagger(torch.nn.Module):
    def __init__(
        self,
        embeddings: torch.tensor,
        hidden_size: int,
        num_layers: int,
        dropout: float,
        bidirectional: bool,
        num_class: int,
    ) -> None:

        super(SlottTagger, self).__init__()
        self.embed = nn.Embedding.from_pretrained(embeddings, freeze=False)
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.D = 2 if bidirectional else 1

        input_size = embeddings.shape[1]
        num_class += 1

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True,
                            dropout=dropout, bidirectional=bidirectional)
        
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True,
                            dropout=dropout, bidirectional=bidirectional)

        self.ln = nn.LayerNorm(input_size)

        self.fc1 = nn.Sequential(
            nn.Linear(hidden_size*self.D, hidden_size),
        )
        self.bn = nn.BatchNorm1d(hidden_size)
        self.fc2 = nn.Sequential(
            # nn.ReLU(),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_class)
        )

    def forward(self, batch) -> torch.Tensor:

        embed_batch = self.embed(batch)
        embed_batch = self.ln(embed_batch)

        output, (h_n, c_n) = self.lstm(embed_batch)
        
        out = self.fc1(output)
        out = self.bn(out.permute(0,2,1))
        out = self.fc2(out.permute(0,2,1))
        
        out = torch.permute(out, (0, 2, 1))

        return out
