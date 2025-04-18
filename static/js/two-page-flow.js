// static/js/two-page-flow.js
document.addEventListener('DOMContentLoaded', function() {
    // Determine which page we're on
    const isContextPage = window.location.pathname === '/' || window.location.pathname === '/context';
    const isContentPage = window.location.pathname === '/generate-content';
    
    // Context page functionality
    if (isContextPage) {
        setupContextPage();
    }
    
    // Content generation page functionality
    if (isContentPage) {
        setupContentPage();
    }
    
    // Setup for the context page (first page)
    function setupContextPage() {
        const contextForm = document.getElementById('contextForm');
        const nextBtn = document.getElementById('nextBtn');
        const resetContextBtn = document.getElementById('resetContextBtn');
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
        nextBtn.addEventListener('click', function() {            
            // Store context data in sessionStorage
            const contextData = {
                hasContextFile: uploadedContextFile !== null,
                contextFileName: uploadedContextFile ? uploadedContextFile.name : null,
                profileUrl: document.getElementById('profileUrl').value,
                scrapeUrl: document.getElementById('scrapeUrl').value,
                scrapePrompt: document.getElementById('scrapePrompt').value || 'Extract the main content from this page'
            };
            
            sessionStorage.setItem('contextData', JSON.stringify(contextData));
            
            // If there's a file, we need to handle it specially
            if (uploadedContextFile) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Store the file content as a base64 string
                    sessionStorage.setItem('contextFileContent', e.target.result);
                    // Navigate to the content generation page
                    window.location.href = '/generate-content';
                };
                reader.readAsDataURL(uploadedContextFile);
            } else {
                // No file, just navigate
                window.location.href = '/generate-content';
            }
        });
        
        // Reset context form
        resetContextBtn.addEventListener('click', function() {
            // Reset file upload
            contextFileUpload.value = '';
            fileNameDisplay.textContent = '';
            fileNameDisplay.classList.remove('visible');
            uploadedContextFile = null;
            
            // Reset scraping fields
            document.getElementById('profileUrl').value = '';
            document.getElementById('scrapeUrl').value = '';
            document.getElementById('scrapePrompt').value = '';
            document.getElementById('scrapingContainer').style.display = 'none';
            
            // Hide error if shown
            document.getElementById('contextError').style.display = 'none';
        });
    }
    
    // Setup for the content generation page (second page)
    function setupContentPage() {
        // Check if we have context data from the previous page
        const contextDataString = sessionStorage.getItem('contextData');
        if (!contextDataString) {
            // No context data, redirect to the context page
            window.location.href = '/';
            return;
        }
        
        const contextData = JSON.parse(contextDataString);
        
        // Add a back button to return to context page
        const contentForm = document.getElementById('contentForm');
        const backButton = document.createElement('button');
        backButton.type = 'button';
        backButton.id = 'backBtn';
        backButton.className = 'btn-secondary';
        backButton.textContent = 'Back to Context';
        contentForm.insertBefore(backButton, contentForm.firstChild);
        
        // Back button click handler
        backButton.addEventListener('click', function() {
            window.location.href = '/';
        });
        
        // Modify the generate button click handler to include context data
        const generateBtn = document.getElementById('generateBtn');
        const originalClickHandler = generateBtn.onclick;
        generateBtn.onclick = null;
        
        generateBtn.addEventListener('click', function() {
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

            // Add context data from the first page
            formData.append('profileUrl', contextData.profileUrl);
            formData.append('scrapeUrl', contextData.scrapeUrl);
            formData.append('scrapePrompt', contextData.scrapePrompt);
            
            // Add context file if it exists
            if (contextData.hasContextFile) {
                const contextFileContent = sessionStorage.getItem('contextFileContent');
                if (contextFileContent) {
                    // Convert base64 back to a file
                    const byteString = atob(contextFileContent.split(',')[1]);
                    const mimeType = contextFileContent.split(',')[0].split(':')[1].split(';')[0];
                    const ab = new ArrayBuffer(byteString.length);
                    const ia = new Uint8Array(ab);
                    for (let i = 0; i < byteString.length; i++) {
                        ia[i] = byteString.charCodeAt(i);
                    }
                    const blob = new Blob([ab], {type: mimeType});
                    const file = new File([blob], contextData.contextFileName, {type: mimeType});
                    formData.append('context_file', file);
                }
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
                    // Display result
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
    }
});