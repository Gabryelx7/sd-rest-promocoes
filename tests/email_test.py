from dotenv import load_dotenv 
import os
import resend

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

params: resend.Emails.SendParams = {
    "from": "Acme <onboarding@resend.dev>",
    "to": ["pdias.2003@alunos.utfpr.edu.br"],
    "subject": "hello world",
    "html": "<strong>it works!</strong>",
}

email = resend.Emails.send(params)
print(email)