<p align="center">
  <img src="https://raw.githubusercontent.com/drona-gyawali/My-Github-Assest/refs/heads/main/dumps/linkly.png" alt="Linkly Banner" width="800" height="160"/>
</p>


**Linkly** is a fast and lightweight URL shortener app built with **FastAPI** and **MongoDB**. It allows you to shorten long URLs, track analytics like number of clicks, and seamlessly handle redirections. Linkly is designed to be minimal, efficient, and developer-friendly.

---

## Features

* **URL Shortening** – Convert long URLs into short, unique IDs
* **Analytics Tracking** – Track number of visits per link (clicks, timestamps, IP, user-agent, etc.)
* **Blazing Fast** – Built with asynchronous FastAPI and Motor for non-blocking MongoDB operations
* **MongoDB Backend** – Fast, scalable, and document-based
* **Dependency Management** – Uses [`uv`](https://github.com/astral-sh/uv) for fast Python dependency resolution

---

> ⚠️ **Note**: Frontend is **not yet added**. However, the backend API is fully functional and tested.

---

## Tech Stack

* **Backend**: Python 3.11+, FastAPI
* **Database**: MongoDB (with Motor)
* **Validation**: Pydantic
* **Dependency Manager**: [`uv`](https://github.com/astral-sh/uv)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/linkly.git
cd linkly
```

### 2. Install Dependencies

Install `uv` if not already installed:

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

Set up a virtual environment and install packages:

```bash
uv venv
source .venv/bin/activate
uv pip install -r uv.lock
```

### 3. Configure Environment

Create a `.env` file:

```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=linkly
IP_DETAILS_URL="http://ip-api.com/json" 
LOCAL_HOST= custom_domain_name
```

---

##  Run the App

```bash
uvicorn app.main:app --reload
```

Visit interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🌐 API Endpoints

### POST `/shorten`

**Request:**

```json
{
  "original_url": "http://127.0.0.1:8000/docs#/Url/create_short_url_shorten_post"
}
```

**Response:**

```json
{
  "short_url": "http://localhost:8000/fzzkpORp6OSlAgqL",
  "original_url": "http://127.0.0.1:8000/docs#/Url/create_short_url_shorten_post"
}
```

---

### GET `/{short_id}`

Redirects to the original URL.

**Example:**

Visiting `http://localhost:8000/fzzkpORp6OSlAgqL` will redirect to:

```
http://127.0.0.1:8000/docs#/Url/create_short_url_shorten_post
```

---

### GET `/analytics/{short_id}`

Returns click analytics.

**Response:**

```json
{
  "_id": "68591a534350e45230df1974",
  "short_id": "http://localhost:8000/fzzkpORp6OSlAgqL",
  "click_details": [
    {
      "user_agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
      "ip": "8.8.8.8",
      "timestamp": "2025-06-23T09:11:47.636000",
      "location": "Ashburn, United States"
    }
  ],
  "clicks": 1
}
```


---

## Running Tests

```bash
pytest
```
