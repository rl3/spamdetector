# spamdetector
An AI based spam detector

This is a test to build an AI based spam detector. **This is currently work progress and by no means suitable for any production use.**

**Most features described below are currently not even remotely implemented nor thought through.**

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
```
cat [the mail to test] | nc -N -U ./spam.sock
```
