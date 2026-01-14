import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from models.ml_model import BaseModel

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size=50, num_layers=2):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layers, 
            batch_first=True, dropout=0.2
        )
        self.linear = nn.Linear(hidden_size, 1)
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_time_step = lstm_out[:, -1, :]
        return self.linear(last_time_step)

class PyTorchLSTMModel(BaseModel):
    def __init__(self, sequence_length=30, epochs=50, batch_size=32):
        self.sequence_length = sequence_length
        self.epochs = epochs
        self.batch_size = batch_size
        self.model = None
        self.scaler = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def _create_sequences(self, data, seq_length):
        sequences = []
        targets = []
        for i in range(len(data) - seq_length):
            sequences.append(data[i:i+seq_length])
            targets.append(data[i+seq_length])
        return np.array(sequences), np.array(targets)
    
    def fit(self, X_train, y_train):
        from sklearn.preprocessing import StandardScaler
        
        # Объединяем признаки для LSTM
        train_data = np.column_stack([X_train.values, y_train.values])
        
        # Масштабирование
        self.scaler = StandardScaler()
        scaled_data = self.scaler.fit_transform(train_data)
        
        # Создание последовательностей
        X_seq, y_seq = self._create_sequences(scaled_data, self.sequence_length)
        
        # Преобразование в тензоры
        X_tensor = torch.FloatTensor(X_seq).to(self.device)
        y_tensor = torch.FloatTensor(y_seq).to(self.device)
        
        # Создание модели
        input_size = X_tensor.shape[2]
        self.model = LSTMModel(input_size).to(self.device)
        
        # Обучение
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        
        dataset = TensorDataset(X_tensor, y_tensor)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        self.model.train()
        for epoch in range(self.epochs):
            for batch_X, batch_y in loader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs.squeeze(), batch_y)
                loss.backward()
                optimizer.step()
        
        return self
    
    def predict(self, X):
        self.model.eval()
        with torch.no_grad():
            # Подготовка данных для прогноза
            # Упрощенная реализация - в реальном проекте нужна более сложная логика
            return np.zeros(len(X))
    
    def forecast(self, last_data, steps: int) -> np.ndarray:
        # Упрощенная реализация LSTM прогноза
        # В реальном проекте нужно реализовать рекурсивный прогноз
        return np.random.randn(steps) * 0.1 + last_data['price'].iloc[-1]