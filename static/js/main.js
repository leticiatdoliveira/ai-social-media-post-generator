// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Settings modal functionality
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    const closeBtn = document.querySelector('.close');
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    
    // Load saved settings if they exist
    loadSettings();
    
    // Show the settings modal when the settings button is clicked
    settingsBtn.addEventListener('click', function() {
        settingsModal.style.display = 'block';
    });
    
    // Close the modal when the close button is clicked
    closeBtn.addEventListener('click', function() {
        settingsModal.style.display = 'none';
    });
    
    // Close the modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });
    
    // Save settings when the save button is clicked
    saveSettingsBtn.addEventListener('click', function() {
        saveSettings();
        settingsModal.style.display = 'none';
    });
    
    // Function to save settings to localStorage
    function saveSettings() {
        const settings = {
            provider: 'openai', // Always use OpenAI
            openai: {
                apiKey: document.getElementById('openaiApiKey').value,
                model: document.getElementById('openaiModel').value
            }
        };
        
        localStorage.setItem('aiSettings', JSON.stringify(settings));
    }
    
    // Function to load settings from localStorage
    function loadSettings() {
        const savedSettings = localStorage.getItem('aiSettings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            
            // Load OpenAI settings
            document.getElementById('openaiApiKey').value = settings.openai?.apiKey || '';
            document.getElementById('openaiModel').value = settings.openai?.model || 'gpt-3.5-turbo';
        }
    }

    // Context file upload handling
    const contextFileUpload = document.getElementById('contextFile');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    let uploadedContextFile = null;

    // Handle context file upload
    contextFileUpload.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            uploadedContextFile = file;
            fileNameDisplay.textContent = file.name;
            fileNameDisplay.classList.add('visible');
        } else {
            uploadedContextFile = null;
            fileNameDisplay.textContent = '';
            fileNameDisplay.classList.remove('visible');
        }
    });

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
        const description = document.getElementById('description').value;
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

        // Create FormData for file upload
        const formData = new FormData();
        formData.append('subject', subject);
        formData.append('description', description);
        formData.append('platform', platform);
        formData.append('tone', tone);
        formData.append('includeHashtags', includeHashtags);
        formData.append('maxHashtags', maxHashtags);
        
        // Get OpenAI settings from localStorage
        const savedSettings = localStorage.getItem('aiSettings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            formData.append('provider', 'openai'); // Always use OpenAI
            
            formData.append('openai_api_key', settings.openai?.apiKey || '');
            formData.append('openai_model', settings.openai?.model || 'gpt-3.5-turbo');
        }

        // Add context file if it exists
        if (uploadedContextFile) {
            formData.append('context_file', uploadedContextFile);
        }

        // Call API with FormData
        fetch('/generate', {
            method: 'POST',
            body: formData,
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

        // Reset context file upload
        contextFileUpload.value = '';
        fileNameDisplay.textContent = '';
        fileNameDisplay.classList.remove('visible');
        uploadedContextFile = null;

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
        // Get AI provider settings from localStorage
        const savedSettings = localStorage.getItem('aiSettings');
        let requestBody = {
            original_content: content,
            feedback: feedback
        };
        
        // Add OpenAI settings to the request body
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            requestBody.provider = 'openai'; // Always use OpenAI
            requestBody.openai_api_key = settings.openai?.apiKey || '';
            requestBody.openai_model = settings.openai?.model || 'gpt-3.5-turbo';
        }
        
        fetch('/submit-feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
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