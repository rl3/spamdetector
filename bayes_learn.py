import re
from collections import defaultdict

class NaiveBayesSpamDetector:
    def __init__(self, n=1):
        self.n = n
        self.spam_word_counts = defaultdict(int)
        self.ham_word_counts = defaultdict(int)
        self.spam_total_words = 0
        self.ham_total_words = 0

    def train(self, emails, labels):
        for email, label in zip(emails, labels):
            words = self._preprocess(email)
            ngrams = self._generate_ngrams(words)
            if label == 'spam':
                for ngram in ngrams:
                    self.spam_word_counts[ngram] += 1
                    self.spam_total_words += 1
            else:
                for ngram in ngrams:
                    self.ham_word_counts[ngram] += 1
                    self.ham_total_words += 1

    def predict(self, email):
        words = self._preprocess(email)
        ngrams = self._generate_ngrams(words)
        spam_score = self._calculate_score(ngrams, self.spam_word_counts, self.spam_total_words)
        ham_score = self._calculate_score(ngrams, self.ham_word_counts, self.ham_total_words)
        return 'spam' if spam_score > ham_score else 'ham'

    def _preprocess(self, email):
        # Preprocess the email by removing special characters, converting to lowercase, etc.
        email = email.lower()
        email = re.sub(r'[^a-zA-Z0-9\s]', '', email)
        words = email.split()
        return words

    def _generate_ngrams(self, words):
        # Generate n-grams from the list of words
        ngrams = []
        for i in range(len(words) - self.n + 1):
            ngram = ' '.join(words[i:i+self.n])
            ngrams.append(ngram)
        return ngrams

    def _calculate_score(self, ngrams, word_counts, total_words):
        # Calculate the score for a given set of n-grams
        score = 0
        for ngram in ngrams:
            count = word_counts[ngram]
            score += count / total_words
        return score

# Example usage
emails = [
    "Get a free iPhone now!",
    "Congratulations! You've won a million dollars!",
    "Hi, how are you doing today?",
    "Reminder: Your appointment is tomorrow."
]
labels = ['spam', 'spam', 'ham', 'ham']

# Create and train the spam detector
detector = NaiveBayesSpamDetector(n=2)
detector.train(emails, labels)

# Test the spam detector
test_email = "Claim your prize now!"
prediction = detector.predict(test_email)
print(f"Prediction: {prediction}")