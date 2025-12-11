from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import os

app = Flask(__name__, static_folder='.')
CORS(app)  # للسماح بالاتصال من الموقع

# تركيب بيانات تدريبية واقعية - 5000 نقطة
np.random.seed(42)
n_samples = 5000

# توليد البيانات
device_type = np.random.choice([0, 1], n_samples, p=[0.3, 0.7])  # 70% أجهزة معروفة
location_match = np.random.choice([0, 1], n_samples, p=[0.25, 0.75])  # 75% مواقع مطابقة
time_anomaly = np.random.choice([0, 1], n_samples, p=[0.8, 0.2])  # 20% أوقات غير عادية
transaction_sensitivity = np.random.choice([0, 1, 2], n_samples, p=[0.4, 0.35, 0.25])  # توزيع متوازن
recent_failed_attempts = np.random.choice([0, 1, 2, 3, 4, 5], n_samples, 
                                          p=[0.5, 0.2, 0.15, 0.1, 0.04, 0.01])  # معظمها 0 محاولات

X_train = np.column_stack([device_type, location_match, time_anomaly, 
                           transaction_sensitivity, recent_failed_attempts])

# حساب Risk Score بناءً على منطق واقعي
risk_scores = []
for i in range(n_samples):
    base_score = 10
    base_score += recent_failed_attempts[i] * 14
    base_score += transaction_sensitivity[i] * 12.5
    if time_anomaly[i] == 1:
        base_score += 20
    if location_match[i] == 0:
        base_score += 10
    if device_type[i] == 0:
        base_score += 10
    noise = np.random.normal(0, 3)
    base_score += noise
    risk_scores.append(max(0, min(100, base_score)))

y_train = np.array(risk_scores)

# تدريب المودل - Random Forest
print("🔄 Training Random Forest model...")
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    min_samples_split=10,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

# طباعة أهمية الميزات
feature_names = ['device_type', 'location_match', 'time_anomaly', 
                'transaction_sensitivity', 'recent_failed_attempts']
feature_importance = model.feature_importances_
print("\n📊 Feature Importance:")
for name, importance in zip(feature_names, feature_importance):
    print(f"   {name}: {importance:.4f} ({importance*100:.2f}%)")

@app.route('/api/calculate-risk', methods=['POST'])
def calculate_risk():
    """
    حساب Risk Score بناءً على البيانات المرسلة
    """
    try:
        data = request.get_json()
        
        # استخراج القيم
        device_type = int(data.get('device_type', 1))
        location_match = int(data.get('location_match', 1))
        time_anomaly = int(data.get('time_anomaly', 0))
        transaction_sensitivity = int(data.get('transaction_sensitivity', 0))
        recent_failed_attempts = int(data.get('recent_failed_attempts', 0))
        
        # إنشاء feature vector
        features = np.array([[device_type, location_match, time_anomaly, 
                            transaction_sensitivity, recent_failed_attempts]])
        
        # حساب Risk Score
        risk_score = model.predict(features)[0]
        risk_score = max(0, min(100, int(round(risk_score))))
        
        # تحديد المستوى والتوصية
        if risk_score <= 39:
            level = "low"
            level_ar = "منخفض"
            recommendation = "تنفيذ مباشر - لا توجد مخاطر"
            action = "allow"
        elif risk_score <= 74:
            level = "medium"
            level_ar = "متوسط"
            recommendation = "يتطلب تحقق إضافي (OTP، بصمة)"
            action = "verify"
        else:
            level = "high"
            level_ar = "مرتفع"
            recommendation = "إيقاف العملية ومراجعة أمنية"
            action = "block"
        
        response = {
            'success': True,
            'risk_score': risk_score,
            'level': level,
            'level_ar': level_ar,
            'recommendation': recommendation,
            'action': action,
            'input_data': {
                'device_type': device_type,
                'location_match': location_match,
                'time_anomaly': time_anomaly,
                'transaction_sensitivity': transaction_sensitivity,
                'recent_failed_attempts': recent_failed_attempts
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/health', methods=['GET'])
def health_check():
    """فحص حالة الـ API"""
    return jsonify({
        'status': 'healthy',
        'message': 'Risk Score API is running',
        'model': 'Random Forest',
        'training_samples': 5000
    })

@app.route('/api/model-info', methods=['GET'])
def model_info():
    """معلومات عن المودل"""
    feature_names = ['device_type', 'location_match', 'time_anomaly', 
                    'transaction_sensitivity', 'recent_failed_attempts']
    feature_importance = model.feature_importances_
    
    return jsonify({
        'model_type': 'Random Forest Regressor',
        'n_estimators': 100,
        'training_samples': 5000,
        'feature_importance': {
            name: float(importance) for name, importance in zip(feature_names, feature_importance)
        }
    })

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """خدمة الملفات الثابتة"""
    try:
        return send_from_directory('.', path)
    except:
        return "File not found", 404

if __name__ == '__main__':
    print("🚀 Starting Nabahah Risk Score API...")
    print("🌲 Model: Random Forest Regressor")
    print(f"📊 Training samples: 5000")
    print(f"🎯 Model R² Score: {model.score(X_train, y_train):.4f}")
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 API will be available at: http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
