# 💰 FinOps Toolkit for Intelligent Cloud Cost Anomaly Detection

> An AI-powered FinOps dashboard that detects cloud cost anomalies using **Facebook Prophet**, performs **Root Cause Analysis (RCA)**, and provides interactive visualizations for cloud cost optimization.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Prophet](https://img.shields.io/badge/ML-Facebook%20Prophet-orange)
![Chart.js](https://img.shields.io/badge/Chart.js-Visualization-red)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## 📌 Overview

Cloud infrastructure costs often increase unexpectedly due to resource misconfigurations, traffic spikes, over-provisioning, or security incidents.

**FinOps Toolkit** is an intelligent cloud cost monitoring system that predicts expected cloud spending using **Facebook Prophet**, identifies abnormal cost spikes, performs **Root Cause Analysis (RCA)**, and presents insights through an interactive dashboard.

I contributed to the design, development, machine learning integration, dashboard implementation, and overall enhancement of the project.

The project combines **Machine Learning**, **Cloud Cost Analytics**, and **FinOps principles** into a simple yet powerful web application.

---

## ✨ Features

- 📈 Prophet-based cloud cost forecasting
- 🚨 Intelligent anomaly detection
- 🔍 Root Cause Analysis (Service, Region & Tags)
- 📊 Interactive dashboard using Chart.js
- 📉 Unit Cost Trend visualization
- 🎚 Adjustable anomaly sensitivity
- 🔐 Role-Based Access (Viewer/Admin)
- ⚠ Security alert banner for high-severity anomalies
- 📥 Export anomaly report as CSV
- 🌐 REST API using FastAPI

---

## 🏗 System Architecture

```
                HTML / CSS / JavaScript Dashboard
                           │
                           ▼
                  FastAPI REST Backend
                           │
                           ▼
            Facebook Prophet ML Engine
                           │
                           ▼
                 Cloud Cost CSV Dataset
```

---

## 🧠 Machine Learning

The anomaly detection engine uses **Facebook Prophet** to:

- Learn cloud spending trends
- Capture seasonal patterns
- Forecast expected cloud costs
- Detect abnormal spending spikes
- Classify anomaly severity

Unlike traditional threshold-based monitoring, Prophet dynamically predicts expected cloud costs based on historical behavior.

---

## 📂 Project Structure

```
Finops-Toolkit
│
├── backend-java/
├── dashboard-frontend/
│   └── index.html
│
├── ml-service-python/
│   ├── ml_service.py
│   ├── cost-analysis.csv
│   └── requirements.txt
│
└── README.md
```

---

## 🛠 Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript
- Chart.js

### Backend
- Python
- FastAPI
- Uvicorn

### Machine Learning
- Facebook Prophet
- Pandas
- NumPy

### Deployment
- Render (Backend)
- GitHub Pages (Frontend)

### Tools
- Git
- GitHub
- VS Code

---

## 📊 Dashboard Modules

### Cost Trend Analysis
Visualizes daily cloud spending and expected spending predicted by Prophet.

### Anomaly Detection
Highlights abnormal cloud cost spikes using ML forecasting.

### Root Cause Analysis
Identifies:
- Top Costly Service
- Top Region
- Top Resource Tag

### Unit Cost Monitoring
Displays cost per business unit over time.

### Security Alerts
Flags high-severity anomalies that may indicate:

- Misconfigured resources
- Unexpected scaling
- Cost leaks
- Suspicious cloud activity

---

## 🔐 Security Features

- Role-Based Access Control (Viewer/Admin)
- ML-based anomaly alerts
- Security risk notifications
- API-based architecture
- Extendable authentication framework

---

## 📈 Future Enhancements

- Docker containerization
- Spring Boot API Gateway
- JWT Authentication
- API Key Security
- Multi-cloud support (AWS, Azure & GCP)
- Real-time billing integration
- Email & Slack alerts
- Cost optimization recommendations

---

## 🚀 Getting Started

### Clone Repository

```bash
git clone https://github.com/Ishwari345/Finops-Toolkit.git
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Backend

```bash
uvicorn ml_service:app --reload --port 8000
```

### Launch Dashboard

Open

```
dashboard-frontend/index.html
```

in your browser.

---

## 📷 Screenshots

> Add screenshots after deployment.

- Dashboard
- Prophet Forecast
- Root Cause Analysis
- Security Alerts

---

## 🎯 Project Objectives

- Detect abnormal cloud spending
- Reduce unnecessary cloud costs
- Improve cloud financial visibility
- Support FinOps decision-making
- Demonstrate ML-driven cloud cost optimization

---

## 👩‍💻 Author

**Ishwari Bagewadi**

GitHub: https://github.com/Ishwari345

---

## 🙏 Acknowledgements

- Facebook Prophet
- FastAPI
- Chart.js
- FinOps Foundation
- Open Source Community

---

