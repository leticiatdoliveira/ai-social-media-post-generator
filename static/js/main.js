// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize step tracking
    let currentStep = 1;
    const totalSteps = 2;
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
            },
            scrapegraph: {
                apiKey: document.getElementById('scrapegraphApiKey').value,
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
            document.getElementById('scrapegraphApiKey').value = settings.scrapegraph?.apiKey || '';
            document.getElementById('openaiApiKey').value = settings.openai?.apiKey || '';
            document.getElementById('openaiModel').value = settings.openai?.model || 'gpt-3.5-turbo';
        }
    }

    // Initialize form sections
    const contextSection = document.getElementById('contextSection');
    const contentSection = document.getElementById('contentSection');
    const stepIndicators = document.querySelectorAll('.step-indicator .step');
    
    // Show the appropriate section based on current step
    function updateStepDisplay() {
        // Update step indicators
        stepIndicators.forEach((step, index) => {
            if (index + 1 === currentStep) {
                step.classList.add('active');
            } else {
                step.classList.remove('active');
            }
        });
        
        // Show/hide appropriate sections
        if (currentStep === 1) {
            contextSection.style.display = 'block';
            contentSection.style.display = 'none';
        } else {
            contextSection.style.display = 'none';
            contentSection.style.display = 'block';
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
    
    // Next button click handler
    document.getElementById('nextBtn').addEventListener('click', function() {
        currentStep = 2;
        updateStepDisplay();
    });
    
    // Back button click handler
    document.getElementById('backBtn').addEventListener('click', function() {
        currentStep = 1;
        updateStepDisplay();
    });
    
    // Reset context form
    document.getElementById('resetContextBtn').addEventListener('click', function() {
        // Reset file upload
        contextFileUpload.value = '';
        fileNameDisplay.textContent = '';
        fileNameDisplay.classList.remove('visible');
        uploadedContextFile = null;
        
        // Reset scraping fields
        document.getElementById('profileUrl').value = '';
        document.getElementById('scrapeUrl').value = '';
        document.getElementById('scrapePrompt').value = '';
        
        // Hide error if shown
        document.getElementById('contextError').style.display = 'none';
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

        // Create FormData for submission
        const formData = new FormData();
        formData.append('subject', subject);
        formData.append('description', description);
        formData.append('platform', platform);
        formData.append('tone', tone);
        formData.append('includeHashtags', includeHashtags);
        formData.append('maxHashtags', maxHashtags.toString());
        
        // Get OpenAI settings from localStorage
        const savedSettings = localStorage.getItem('aiSettings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            formData.append('provider', 'openai'); // Always use OpenAI
            
            formData.append('openai_api_key', settings.openai?.apiKey || '');
            formData.append('openai_model', settings.openai?.model || 'gpt-3.5-turbo');

            formData.append('scrapegraph_api_key', settings.scrapegraph?.apiKey || '');
        }

        // Add context file if it exists
        if (uploadedContextFile) {
            formData.append('context_file', uploadedContextFile);
        }
        
        // Add context data from the first step
        const profileUrl = document.getElementById('profileUrl').value;
        const scrapeUrl = document.getElementById('scrapeUrl').value;
        const scrapePrompt = document.getElementById('scrapePrompt').value;
        formData.append('profileUrl', profileUrl);
        formData.append('scrapeUrl', scrapeUrl);
        formData.append('scrapePrompt', scrapePrompt || 'Extract the main content from this page');

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
        
        // Reset scraping fields
        document.getElementById('scrapeUrl').value = '';
        document.getElementById('scrapePrompt').value = '';
        document.getElementById('scrapingContainer').style.display = 'none';

        // Hide results
        document.getElementById('result').style.display = 'none';
        document.getElementById('error').style.display = 'none';

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
});
