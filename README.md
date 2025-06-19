# 💸 Hub Monetization Insights

This project simulates an end-to-end monetization analytics stack for a B2B SaaS company like HubSpot. It includes synthetic quote-to-cash data, pricing elasticity models, competitive pricing benchmarks, and an executive-facing dashboard.

---

## 🚀 Features

- Customer usage & churn simulation
- Price elasticity modeling per product/tier
- LTV & retention metrics
- Competitive pricing benchmarks
- Streamlit dashboard with dynamic filters
- dbt data models & Airflow orchestration
- Executive pricing proposal (Markdown)

---

## 🛠️ Installation

1. **Clone or extract the repository:**

```bash
# If using Git:
git clone https://github.com/your-username/hub-monetization-insights.git
cd hub-monetization-insights

# OR unzip manually:
unzip hub-monetization-insights.zip
cd hub-monetization-insights
```

2. **Install dependencies (create a virtual environment recommended):**

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

3. **Run the Streamlit dashboard:**

```bash
streamlit run dashboard/streamlit_app.py
```

---

## 🧠 Analytics Stack

- **Python**: Data simulation & modeling
- **dbt**: SQL transformations (`dbt_models/`)
- **Airflow**: Simulated DAG in `airflow_dags/`
- **Streamlit**: Dashboard UI
- **Jupyter**: Exploratory notebooks

---

## 🧾 Executive Proposal

See `docs/Pricing_Proposal.md` for a sample leadership-facing pricing strategy document.

---

## 🗃️ Uploading to GitHub

If you downloaded the `.zip` file and extracted locally:

1. Initialize a Git repo:

```bash
cd hub-monetization-insights
git init
git add .
git commit -m "Initial commit"
```

2. Create a new repo on GitHub (via browser or CLI).

3. Connect and push:

```bash
git remote add origin https://github.com/your-username/hub-monetization-insights.git
git branch -M main
git push -u origin main
```

---

## 📬 Feedback

Feel free to fork, customize, and share feedback or enhancements!

---

