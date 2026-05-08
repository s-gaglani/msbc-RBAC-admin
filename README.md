# CommonAdminService
 
## 🚀 Setup Instructions
 
1. Create virtual environment
   `python -m venv venv`
   
2. Activate the virtual environment
   `venv\Scripts\activate`
 
3. Install dependencies
   `pip install -r requirements.txt`

4. Update .env file
 
5. Start development server
   `python manage.py runserver`
 
## 🧱 Apps Included

 
 
## Use uv instead of pip
 
1. Install uv(if not installed)
   `pip install uv`
 
2. Sync the latest libraries added
   `uv init`

3. Install dependencies
   `uv add -r requirements.txt`

4. Update .env file

5. Run migrations
   `uv run manage.py migrate`
 
6. Start development server
   `uv run manage.py runserver`
 