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


---

## 🗺️ Geographic Map Interaction

Inside the **"Geo View" tab** of the dashboard:

- Use the **Map Mode toggle** to switch between:
  - 🌍 Global map (by country)
  - 🗺️ USA state-level map
- Hover over regions to see customer counts
- The map updates dynamically based on selected mode

---

## 🚀 Deploying to Streamlit Cloud

To deploy this app to [Streamlit Cloud](https://streamlit.io/cloud):

1. **Push this project to GitHub** (already done)
2. Go to [https://streamlit.io/cloud](https://streamlit.io/cloud)
3. Click **"New app"** and connect your GitHub repository
4. Set the file path to:
   ```bash
   dashboard/streamlit_app.py
   ```
5. Click **Deploy**

✅ Your app will be live at:
`https://your-username.streamlit.app/hub-monetization-insights`

Optional: Add environment variables or secrets using the **Secrets Manager** in Streamlit Cloud if needed (not required for this project).

---

