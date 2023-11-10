# spamdetector
An AI based spam detector

This is a test to build an AI based spam detector. **This is currently work progress and by no means suitable for any production use.**

**Most features described below are currently not even remotely implemented nor thought through.**

## Installation
In the project directory run
```
python -m venv .venv
```
activate the environment
```
source .venv/bin/activate
```
and install the dependecies
```
pip install -r requirements.txt
```
To start a script, you can use the `start` script. That activates the environment and executes the requested script and passes optional parameters.

## Planned Features
- Command line program to be run on a regular basis (daily?) on messages known as SPAM (i.e. spam or junk folder) and
messages known as HAM (i.e. seen and worked with mails not classified as spam, i.e. mails in sub folders) to train the model.
- Fetch those mails from an IMAP server to classify mails in the top INBOX folder that where replied to as ham.
- A daemon to be contacted by postfix (or may be other SMTP servers, contacted via unix socket or TCP port) to classify incoming mails based on the training.
- Hot reload the trained model after training with new mails


## Train the model
To train the model you should run `spam-learn.py [mail directory]`.

- Mails in folders containing words 'Trash' or 'Deleted' are ignored.
- Mails in folders containing words 'Spam' will be treated as SPA;
- All other mails are treated as HAM

## Test Spam Detection
To test the mail server, there is a mail source `test_mail_source.py` to simulate an incoming mail message and a mail sink `test_mail_sink.py` to display the message returned by the spamdetector.

Both scripts use the settings from `config.py`.

To start the mail sink
```
./start test_mail_sink.py
```
To start the spamdetector
```
./start ai_filter_mail_daemon.py
```
You can now simulate sending a mail with a sender and one (or more) recipients with
```
./start test_mail_source.py sender@example.com recipient1@example.com recipient2@example.com < mail_body.txt
```

## Postfix integration
To pass incoming mails to the spam detector, you need to add the following lines to postfix's `main.cf`:
```
content_filter = scanner:[127.0.0.1]:10025
```
And to `master.cf` add the following block to reinject parsed mails
```
# reinject from spam filter
127.0.0.1:10026 inet n  -       n       -       -       smtpd
    -o content_filter=
    -o myhostname=post-spamdetection
    -o local_recipient_maps=
    -o relay_recipient_maps=
    -o mynetworks=127.0.0.1/32,[::1]/128
    -o mynetworks_style=subnet
    -o smtpd_restriction_classes=
    -o smtpd_client_restrictions=
    -o smtpd_helo_restrictions=
    -o smtpd_sender_restrictions=
    -o smtpd_recipient_restrictions=permit_mynetworks,reject
```
Please replace port numbers `10025` and `10026` with ports set in `config.py`!

The port mentioned in `content_filter` is the port spamdetector is listeining on and the port from `master.cf` is the port spamdetector forwards it's mails to.
