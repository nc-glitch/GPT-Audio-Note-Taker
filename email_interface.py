import imaplib
import stmplib
import email
from email.mime.text import MIMEText

email = 'auto.note.gpt@gmail.com'
pssd = 'noteTaking1!'
server = 'gmail.com'

def read_emails():
    mail