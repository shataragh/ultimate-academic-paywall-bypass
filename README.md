# 🧠 Ultimate Academic Paywall Bypass

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Open Access](https://img.shields.io/badge/Open%20Science-Supported-orange)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

> 🚀 A smart, multi-source DOI resolver that helps researchers ethically access academic papers from open-access platforms and archives.

---

## 📚 Overview

Academic research should be accessible to everyone. This Python tool helps bypass paywalls **legally and ethically** by searching across trusted open-access repositories, author uploads, and archival services. It uses robust scraping, API calls, and intelligent heuristics to locate full-text PDFs of scholarly articles.

---

## ✨ Features

- 🔍 **DOI Validation & Extraction**  
  Accepts raw DOIs or DOI URLs and cleans them for processing.

- 🌐 **Multi-Source Search**  
  Queries APIs and scrapes platforms like:
  - Unpaywall
  - CORE
  - bioRxiv
  - Zenodo
  - ResearchGate
  - Wayback Machine
  - Author profiles via Google

- 🔁 **Retry Logic & Logging**  
  Handles timeouts and failures gracefully with exponential backoff and logs all activity to `paywall_bypass.log`.

- ⚠️ **Optional Sci-Hub Fallback**  
  Included for educational purposes only. Use responsibly and at your own discretion.

---

## 🛠️ Installation

```bash
git clone https://github.com/yourusername/ultimate-academic-paywall-bypass.git
cd ultimate-academic-paywall-bypass
pip install -r requirements.txt
