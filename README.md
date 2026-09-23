# SmartCropAdvisorySystem
# 🌱 SmartCrop

**SmartCrop**   is an intelligent agriculture-based application designed to help farmers make better crop-related decisions using **machine learning, environmental data, and smart recommendations**.

The system analyzes relevant agricultural parameters and provides suitable crop recommendations, helping improve productivity and reduce the risk of choosing unsuitable crops.

---

## 🚀 Features

* 🌾 **Crop Recommendation**
  Recommends suitable crops based on agricultural and environmental conditions.

* 🤖 **Machine Learning Prediction**
  Uses machine learning models to analyze input parameters and generate predictions.

* 🌱 **Smart Agricultural Insights**
  Helps users understand which crops may be more suitable for the given conditions.

* 📊 **Data-Based Decision Making**
  Uses soil and environmental parameters rather than relying only on manual assumptions.

* 💻 **User-Friendly Interface**
  Simple interface for entering agricultural parameters and viewing recommendations.

* ⚡ **Fast Predictions**
  Provides crop recommendations quickly after receiving the required inputs.

* 🎙️ **Multilingual Voice Assistant (Speech-to-Speech & Speech-to-Text)**
  Speak naturally in Telugu (తెలుగు), Hindi (हिंदी), or English. Uses the browser's Web Speech API with no external API keys required, providing spoken audio advice for hands-free field use.

* 📲 **WhatsApp & Telegram Advisory Bot & Simulator**
  Connects farmers directly over WhatsApp (Twilio/Meta) and Telegram. Supports commands (`weather`, `recommend`, `tips`) and leaf photo disease inspection. Includes an in-app interactive smartphone simulator.

* 📄 **One-Click Soil Health & Advisory PDF Report**
  Generates an official, printable PDF Soil Health Card containing measured field conditions, top-ranked crop matches, tailored NPK fertilizer guidance, and irrigation schedules.

---

## 🧠 How It Works

The basic workflow of SmartCrop is:

```text
User Input
    ↓
Soil & Environmental Parameters
    ↓
Data Preprocessing
    ↓
Machine Learning Model
    ↓
Prediction
    ↓
Recommended Crop
```

The user provides the required parameters, which are processed and passed to the trained machine learning model. The model then predicts the most suitable crop based on the provided conditions.

---

## 📥 Input Parameters

Depending on the model implementation, SmartCrop can use parameters such as:

| Parameter      | Description                 |
| -------------- | --------------------------- |
| Nitrogen (N)   | Nitrogen content in soil    |
| Phosphorus (P) | Phosphorus content in soil  |
| Potassium (K)  | Potassium content in soil   |
| Temperature    | Current/average temperature |
| Humidity       | Humidity level              |
| pH             | Soil pH value               |
| Rainfall       | Expected rainfall           |

---

## 🛠️ Tech Stack

### Frontend

* Flutter / Web Interface

### Backend

* Python
* Flask / FastAPI

### Machine Learning

* Python
* Pandas
* NumPy
* Scikit-learn

### Database

* MongoDB / Firebase

### Development Tools

* Git
* GitHub
* VS Code
* Jupyter Notebook

---

## 📂 Project Structure

```text
SmartCrop/
│
├── frontend/
│   ├── lib/
│   ├── assets/
│   └── ...
│
├── backend/
│   ├── app.py
│   ├── models/
│   ├── routes/
│   └── ...
│
├── ml/
│   ├── dataset/
│   ├── notebooks/
│   ├── train.py
│   └── model.pkl
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/SmartCrop.git
```

```bash
cd SmartCrop
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Backend

```bash
python app.py
```

### 5. Run the Frontend

If using Flutter:

```bash
flutter pub get
flutter run
```

---

## 🤖 Machine Learning Workflow

The machine learning pipeline consists of the following steps:

```text
Dataset
   ↓
Data Cleaning
   ↓
Exploratory Data Analysis
   ↓
Feature Selection
   ↓
Data Preprocessing
   ↓
Model Training
   ↓
Model Evaluation
   ↓
Model Selection
   ↓
Prediction
```

The trained model is integrated with the application so that users can receive predictions through the application interface.

---

## 📊 Model Evaluation

The machine learning model can be evaluated using metrics such as:

* Accuracy
* Precision
* Recall
* F1-Score
* Confusion Matrix

Different classification algorithms can be compared to select the model that provides the best performance for crop recommendation.

---

## 🎯 Objective

The main objective of SmartCrop is to:

> **Use technology and machine learning to provide data-driven crop recommendations and support smarter agricultural decision-making.**

The project aims to reduce uncertainty in crop selection and help farmers make decisions based on soil and environmental conditions.

---

## 🔮 Future Enhancements

Future versions of SmartCrop can include:

* 🌦️ Real-time weather API integration
* 🛰️ Satellite/remote-sensing data
* 🌱 Disease detection using images
* 💧 Irrigation recommendations
* 🧪 Fertilizer recommendations
* 📈 Crop yield prediction
* 💰 Market price prediction
* 🌾 Personalized farming recommendations
* 🗺️ Location-based recommendations
* 🌐 Multi-language support
* 📱 Mobile notifications
* ☁️ Cloud deployment

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/register` | Register farmer account with phone and village |
| `POST` | `/api/login` | Login and obtain session token |
| `GET` | `/api/weather?city=<city>` | Current weather data and conditions |
| `POST` | `/api/recommend` | Crop recommendations based on temp, humidity, pH |
| `POST` | `/api/advisory` | Crop-specific environmental status and guidance |
| `POST` | `/api/ai-advisory` | AI agricultural consultation |
| `POST` | `/api/disease` | Pl@ntNet plant disease leaf image identification |
| `POST` | `/api/voice-advisory` | Multilingual spoken advisory (English, Hindi, Telugu) |
| `POST` | `/api/report/pdf` | Generate & download official Soil Health Card PDF |
| `POST` | `/api/webhook/whatsapp` | WhatsApp bot webhook (Twilio / Meta format) |
| `POST` | `/api/webhook/telegram` | Telegram Bot update webhook |
| `POST` | `/api/bot/simulate` | Interactive in-dashboard bot simulator |

---

## 🔐 Security

* Secure API communication
* Environment variables for sensitive credentials
* Input validation
* Authentication and authorization where required
* Secure database configuration

---

## 🤝 Contribution

Contributions are welcome!

1. Fork the repository.
2. Create a new branch.

```bash
git checkout -b feature/new-feature
```

3. Make your changes.
4. Commit your changes.

```bash
git add .
git commit -m "Add new feature"
```

5. Push the branch.

```bash
git push origin feature/new-feature
```

6. Create a Pull Request.

---

## 📜 License

This project is developed for educational and research purposes.

You can add your preferred license, such as **MIT License**, depending on the project's requirements.

---

## 👨‍💻 Authors

**SmartCrop Team**

Developed as a project focused on applying **Machine Learning and modern technology to agriculture**.

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

**SmartCrop — Making Agriculture Smarter with Technology 🌱🤖**
