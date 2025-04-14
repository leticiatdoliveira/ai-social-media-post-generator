// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Toggle max hashtags field visibility when hashtag checkbox is clicked
    document.getElementById('hashtags').addEventListener('change', function() {
        const container = document.getElementById('maxHashtagsContainer');
        if (this.checked) {
            container.classList.add('visible');
        } else {
            container.classList.remove('visible');
        }
    });

    // Generate content button click event
    document.getElementById('generateBtn').addEventListener('click', function() {
        const subject = document.getElementById('subject').value;
        const platform = document.getElementById('platform').value;
        const tone = document.getElementById('tone').value;
        const includeHashtags = document.getElementById('hashtags').checked;
        const maxHashtags = includeHashtags ?
            parseInt(document.getElementById('maxHashtags').value) || 5 : 0;

        // Form validation
        if (!subject || !platform || !tone) {
            document.getElementById('error').textContent = 'Please fill in all required fields.';
            document.getElementById('error').style.display = 'block';
            return;
        }

        // Hide error if it was shown
        document.getElementById('error').style.display = 'none';

        // Show loader
        document.getElementById('loader').style.display = 'flex';

        // Hide result
        document.getElementById('result').style.display = 'none';

        // Hide feedback container
        document.getElementById('feedback-container').style.display = 'none';

        // Call API
        fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                subject: subject,
                platform: platform,
                tone: tone,
                includeHashtags: includeHashtags,
                maxHashtags: maxHashtags
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Hide loader
            document.getElementById('loader').style.display = 'none';

            if (data.error) {
                // Show error
                document.getElementById('error').textContent = data.error;
                document.getElementById('error').style.display = 'block';
            } else {
                // Always display result, regardless of required_inputs
                document.getElementById('content-display').innerHTML = data.content.replace(/\n/g, '<br>');
                document.getElementById('result').style.display = 'block';
                // Show feedback container only after successful generation
                document.getElementById('feedback-container').style.display = 'block';
            }
        })
        .catch((error) => {
            // Hide loader
            document.getElementById('loader').style.display = 'none';

            // Show error
            document.getElementById('error').textContent = 'Failed to generate content. Please try again later.';
            document.getElementById('error').style.display = 'block';
            console.error('Error:', error);
        });
    });

    // Clear content button click event
    document.getElementById('resetBtn').addEventListener('click', function() {
        // Reset form fields
        document.getElementById('subject').value = '';
        document.getElementById('description').value = '';
        document.getElementById('platform').value = '';
        document.getElementById('tone').value = '';

        // Reset hashtags checkbox and max hashtags
        document.getElementById('hashtags').checked = false;
        document.getElementById('maxHashtags').value = '5';
        document.getElementById('maxHashtagsContainer').classList.remove('visible');

        // Hide results and feedback
        document.getElementById('result').style.display = 'none';
        document.getElementById('error').style.display = 'none';
        document.getElementById('feedback-container').style.display = 'none';
        document.getElementById('feedback-form').style.display = 'none';
        document.getElementById('feedback-success').style.display = 'none';
        document.getElementById('btn-feedback').style.display = 'block';
        document.getElementById('feedback-text').value = '';

        // Clear content
        document.getElementById('content-display').innerHTML = '';
    });

    // Copy to clipboard functionality
    document.getElementById('copyBtn').addEventListener('click', function() {
        const contentText = document.getElementById('content-display').innerText;
        navigator.clipboard.writeText(contentText).then(function() {
            const copyBtn = document.getElementById('copyBtn');
            const originalText = copyBtn.textContent;
            copyBtn.textContent = 'Copied!';
            copyBtn.classList.add('copied');

            setTimeout(function() {
                copyBtn.textContent = originalText;
                copyBtn.classList.remove('copied');
            }, 2000);
        });
    });

    // Feedback form submission
    initFeedback();
});

// Add this function outside the DOMContentLoaded event listener
function initFeedback() {
    const btnFeedback = document.getElementById('btn-feedback');
    const feedbackForm = document.getElementById('feedback-form');
    const btnSubmitFeedback = document.getElementById('btn-submit-feedback');
    const btnCancelFeedback = document.getElementById('btn-cancel-feedback');
    const feedbackSuccess = document.getElementById('feedback-success');

    // Apply button styling
    btnFeedback.classList.add('btn', 'btn-secondary');
    btnSubmitFeedback.classList.add('btn', 'btn-primary');
    btnCancelFeedback.classList.add('btn', 'btn-secondary');

    btnFeedback.addEventListener('click', function() {
        feedbackForm.style.display = 'block';
        btnFeedback.style.display = 'none';
    });

    btnCancelFeedback.addEventListener('click', function() {
        feedbackForm.style.display = 'none';
        btnFeedback.style.display = 'block';
        document.getElementById('feedback-text').value = '';
    });

    btnSubmitFeedback.addEventListener('click', function() {
        const feedback = document.getElementById('feedback-text').value;
        const content = document.getElementById('content-display').textContent;

        if (!feedback.trim()) {
            return;
        }

        // Show mini-loader in the feedback section
        const feedbackLoader = document.createElement('div');
        feedbackLoader.className = 'loader-small';
        feedbackLoader.innerHTML = '<div class="spinner-small"></div><p>Improving your content...</p>';
        feedbackForm.appendChild(feedbackLoader);

        // Disable submit button while processing
        btnSubmitFeedback.disabled = true;

        // Submit feedback and get improved content
        fetch('/submit-feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                original_content: content,
                feedback: feedback
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Remove loader
            feedbackLoader.remove();
            btnSubmitFeedback.disabled = false;

            if (data.improved_content) {
                // Update content with improved version
                document.getElementById('content-display').innerHTML = data.improved_content.replace(/\n/g, '<br>');

                // Show success message
                feedbackForm.style.display = 'none';
                feedbackSuccess.style.display = 'block';
                feedbackSuccess.textContent = 'Content improved based on your feedback!';
            } else {
                feedbackForm.style.display = 'none';
                feedbackSuccess.style.display = 'block';
            }

            setTimeout(() => {
                feedbackSuccess.style.display = 'none';
                btnFeedback.style.display = 'block';
                document.getElementById('feedback-text').value = '';
            }, 3000);
        })
        .catch(error => {
            // Remove loader
            feedbackLoader.remove();
            btnSubmitFeedback.disabled = false;
            console.error('Error submitting feedback:', error);
        });
    });
}