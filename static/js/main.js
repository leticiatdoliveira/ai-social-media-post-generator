// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {   
    // Initialize step tracking
    let currentStep = 1;
    // Settings modal functionality
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    const closeBtn = document.querySelector('.close');
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    // Load saved settings if they exist
    loadSettings();
    
    // Show the settings modal when the settings button is clicked
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent any default behavior
            settingsModal.classList.remove('hidden');
            settingsModal.classList.add('flex');
        });
        
        // Add a direct onclick attribute as a fallback
        settingsBtn.onclick = function() {
            settingsModal.classList.remove('hidden');
            settingsModal.classList.add('flex');
            return false;
        };
    } else {
        console.error('Settings button not found in the DOM');
    }
    
    // Close the modal when the close button is clicked
    closeBtn.addEventListener('click', function() {
        settingsModal.classList.remove('flex');
        settingsModal.classList.add('hidden');
    });
    
    // Close the modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === settingsModal) {
            settingsModal.classList.remove('flex');
            settingsModal.classList.add('hidden');
        }
    });
    
    // Save settings when the save button is clicked
    saveSettingsBtn.addEventListener('click', function() {
        saveSettings();
        settingsModal.classList.remove('flex');
        settingsModal.classList.add('hidden');
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
    const stepIndicators = document.querySelectorAll('.step-indicator');

    updateStepDisplay();
    
    // Show the appropriate section based on current step
    function updateStepDisplay() {
        stepIndicators.forEach((step) => {
            const stepNumber = parseInt(step.getAttribute('data-step'));
            if (stepNumber === currentStep) {
                step.classList.add('bg-primary');
                step.classList.add('text-white');
                step.classList.add('shadow-md');
                step.classList.remove('bg-cardBg');
                step.classList.remove('text-gray-500');
            } else {
                step.classList.remove('bg-primary');
                step.classList.remove('text-white');
                step.classList.remove('shadow-md');
                step.classList.add('bg-cardBg');
                step.classList.add('text-gray-500');
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
            fileNameDisplay.classList.remove('hidden');
        } else {
            uploadedContextFile = null;
            fileNameDisplay.textContent = '';
            fileNameDisplay.classList.add('hidden');
        }
    });
    
    // Next button click handler
    document.getElementById('nextBtn').addEventListener('click', function() {
        currentStep = 2;       // Update step display and hide context inf
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
        document.getElementById('contextError').classList.add('hidden');
    });

    // Toggle max hashtags field visibility when hashtag checkbox is clicked
    document.getElementById('hashtags').addEventListener('change', function() {
        const container = document.getElementById('maxHashtagsContainer');
        if (this.checked) {
            container.classList.remove('hidden');
        } else {
            container.classList.add('hidden');
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
            document.getElementById('error').classList.remove('hidden');
            return;
        }

        // Hide error if it was shown
        document.getElementById('error').classList.add('hidden');

        // Show loader
        document.getElementById('loader').classList.remove('hidden');
        document.getElementById('loader').classList.add('flex');

        // Hide result
        document.getElementById('result').classList.add('hidden');

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
            document.getElementById('loader').classList.add('hidden');
            document.getElementById('loader').classList.remove('flex');

            if (data.error) {
                // Show error
                document.getElementById('error').textContent = data.error;
                document.getElementById('error').classList.remove('hidden');
            } else {
                // Always display result, regardless of required_inputs
                document.getElementById('content-display').innerHTML = data.content.replace(/\n/g, '<br>');
                document.getElementById('result').classList.remove('hidden');
            }
        })
        .catch((error) => {
            // Hide loader
            document.getElementById('loader').classList.add('hidden');
            document.getElementById('loader').classList.remove('flex');

            // Show error
            document.getElementById('error').textContent = 'Failed to generate content. Please try again later.';
            document.getElementById('error').classList.remove('hidden');
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
        document.getElementById('maxHashtagsContainer').classList.add('hidden');

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
        document.getElementById('result').classList.add('hidden');
        document.getElementById('error').classList.add('hidden');

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
