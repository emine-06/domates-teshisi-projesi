import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# 1. Az önce oluşturduğumuz veriyi okuyoruz
df = pd.read_csv('domates_verisi.csv')

# 2. Modeli hazırlıyoruz (X: özellikler, y: sonuç)
X = df.drop('hastalik_var_mi', axis=1)
y = df['hastalik_var_mi']

# 3. Modeli eğitiyoruz (Öğrenme aşaması)
model = RandomForestClassifier()
model.fit(X, y)

# 4. Öğrenilen bilgileri (modeli) kaydediyoruz
joblib.dump(model, 'domates_modeli.pkl')

print("--- MODEL BASARIYLA EGITILDI ---")
print("'domates_modeli.pkl' dosyası oluşturuldu. Artık bir beynimiz var!")