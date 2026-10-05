# anomaly_detector.py
import numpy as np
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

class LSTMAutoencoder(nn.Module):
    def __init__(self, input_dim=6, hidden_dim=32, seq_len=10):
        super().__init__()
        self.encoder = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.decoder = nn.LSTM(hidden_dim, input_dim, batch_first=True)
        self.seq_len = seq_len

    def forward(self, x):
        _, (h, _) = self.encoder(x)
        # h shape: [1, batch_size, hidden_dim]
        # permute to [batch_size, 1, hidden_dim] and repeat to [batch_size, seq_len, hidden_dim]
        h_rep = h.permute(1, 0, 2).repeat(1, self.seq_len, 1)
        out, _ = self.decoder(h_rep)
        return out

class AnomalyDetector:
    def __init__(self, threshold_percentile=95, seq_len=10, epochs=10, batch_size=128):
        self.seq_len = seq_len
        self.model = LSTMAutoencoder(input_dim=6, hidden_dim=32, seq_len=seq_len)
        self.scaler = StandardScaler()
        self.threshold = None
        self.threshold_pct = threshold_percentile
        self.epochs = epochs
        self.batch_size = batch_size
        self.features = ["rsrp", "rsrq", "sinr", "cqi", "latency_ms", "packet_loss"]

    def _create_sequences(self, df_normal, fit_scaler=True):
        # Standardize the features
        if fit_scaler:
            scaled_values = self.scaler.fit_transform(df_normal[self.features].values)
        else:
            scaled_values = self.scaler.transform(df_normal[self.features].values)

        df_scaled = df_normal.copy()
        df_scaled[self.features] = scaled_values

        sequences = []
        # Group by ue_id and sort by timestamp to extract contiguous user-level sequences
        for ue_id, group in df_scaled.groupby("ue_id"):
            group_sorted = group.sort_values("timestamp")
            vals = group_sorted[self.features].values
            for i in range(len(vals) - self.seq_len + 1):
                sequences.append(vals[i : i + self.seq_len])

        return np.array(sequences)

    def train(self, normal_df):
        print("Preprocessing normal dataset for anomaly detection training...")
        seq_data = self._create_sequences(normal_df, fit_scaler=True)
        
        # Convert to PyTorch tensors
        dataset = TensorDataset(torch.tensor(seq_data, dtype=torch.float32))
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        criterion = nn.MSELoss()
        
        self.model.train()
        print(f"Training LSTM Autoencoder for {self.epochs} epochs...")
        for epoch in range(self.epochs):
            total_loss = 0.0
            for batch in dataloader:
                x = batch[0]
                optimizer.zero_grad()
                out = self.model(x)
                loss = criterion(out, x)
                loss.backward()
                optimizer.step()
                total_loss += loss.item() * x.size(0)
            epoch_loss = total_loss / len(dataset)
            print(f"Epoch {epoch+1}/{self.epochs} - Loss: {epoch_loss:.6f}")

        # Compute threshold based on reconstruction errors of training data
        self.model.eval()
        errors = []
        with torch.no_grad():
            for i in range(len(seq_data)):
                x_val = torch.tensor(seq_data[i:i+1], dtype=torch.float32)
                recon = self.model(x_val)
                loss = criterion(recon, x_val).item()
                errors.append(loss)
        
        self.threshold = np.percentile(errors, self.threshold_pct)
        print(f"LSTM Autoencoder training complete. Reconstruction threshold (percentile={self.threshold_pct}): {self.threshold:.6f}")

    def detect(self, window):
        # window: numpy array of shape [1, seq_len, 6] (raw, unscaled)
        self.model.eval()
        with torch.no_grad():
            seq_len, num_features = window.shape[1], window.shape[2]
            # Flatten window to [seq_len, 6] for scaling
            flat_window = window.reshape(-1, num_features)
            scaled_flat = self.scaler.transform(flat_window)
            scaled_window = scaled_flat.reshape(1, seq_len, num_features)
            
            x_tensor = torch.tensor(scaled_window, dtype=torch.float32)
            recon = self.model(x_tensor)
            
            # Compute MSE reconstruction error
            mse = ((x_tensor - recon)**2).mean().item()
            
            is_anomaly = mse > self.threshold if self.threshold is not None else False
            return is_anomaly, mse