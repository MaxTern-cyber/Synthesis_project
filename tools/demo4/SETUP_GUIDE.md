# Gemini AI Agent Setup Guide

## Step 1: Get Your Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

## Step 2: Configure the Application

1. In the `demo2` folder, create a new file named `.env`
2. Add this line to the `.env` file:
   ```
   GEMINI_API_KEY=paste_your_api_key_here
   ```
3. Replace `paste_your_api_key_here` with your actual API key

## Step 3: Install Dependencies

Run in terminal:
```bash
pip install -r requirements_demo2.txt
```

## Step 4: Launch the Application

Run in terminal:
```bash
streamlit run ai_agent_app.py
```

## Security Notes

- Never commit your `.env` file to version control
- The `.env` file is already added to `.gitignore`
- Keep your API key private and secure
