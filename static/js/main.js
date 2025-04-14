// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Toggle max hashtags field visibility when hashtags checkbox is clicked
    document.getElementById('hashtags').addEventListener('change', function() {
        const container = document.getElementById('maxHashtagsContainer');
        if (this.checked) {
            container.classList.add('visible');
        } else {
            container.classList.remove('visible');
        }
    });

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

        // Hide result and clear any previous additional fields
        document.getElementById('result').style.display = 'none';
        const additionalFieldsContainer = document.getElementById('additional-fields');
        if (additionalFieldsContainer) {
            additionalFieldsContainer.innerHTML = '';
        }

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
                // Check if additional inputs are required
                if (data.required_inputs && data.required_inputs.length > 0) {
                    // Don't show result yet, first collect additional inputs
                    displayRequiredInputsForm(data.required_inputs, data.content);
                } else {
                    // No additional inputs needed, display result
                    document.getElementById('content-display').innerHTML = data.content.replace(/\n/g, '<br>');
                    document.getElementById('result').style.display = 'block';
                }
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

// Function to display form for required inputs
function displayRequiredInputsForm(requiredInputs, originalContent) {
    // Create container for additional fields if it doesn't exist
    let additionalFields = document.getElementById('additional-fields');
    if (!additionalFields) {
        additionalFields = document.createElement('div');
        additionalFields.id = 'additional-fields';
        document.querySelector('.container').insertBefore(additionalFields, document.getElementById('result'));
    }
    additionalFields.innerHTML = '';

    // Add title
    const title = document.createElement('h3');
    title.textContent = 'Additional Information Needed';
    additionalFields.appendChild(title);

    // Create form for additional inputs
    const form = document.createElement('form');
    form.id = 'additional-inputs-form';

    requiredInputs.forEach((input, index) => {
        const fieldContainer = document.createElement('div');
        fieldContainer.className = 'form-group';

        const label = document.createElement('label');
        label.setAttribute('for', `additional-input-${index}`);
        label.textContent = input;

        const inputField = document.createElement('input');
        inputField.type = 'text';
        inputField.id = `additional-input-${index}`;
        inputField.name = input;
        inputField.required = true;

        fieldContainer.appendChild(label);
        fieldContainer.appendChild(inputField);
        form.appendChild(fieldContainer);
    });

    // Add submit button
    const submitBtn = document.createElement('button');
    submitBtn.type = 'button';
    submitBtn.className = 'btn-generate';
    submitBtn.textContent = 'Generate Content';
    submitBtn.onclick = function() {
        // Validate all required fields are filled
        const inputs = form.querySelectorAll('input');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.style.borderColor = 'var(--error-color)';
            } else {
                input.style.borderColor = '';
            }
        });

        if (isValid) {
            updateContentWithInputs(originalContent);
        }
    };

    form.appendChild(submitBtn);
    additionalFields.appendChild(form);

    // Hide the result section while collecting inputs
    document.getElementById('result').style.display = 'none';
}

function updateContentWithInputs(originalContent) {
    // Get all additional inputs
    const form = document.getElementById('additional-inputs-form');
    const inputs = form.querySelectorAll('input');

    // Show loader again while processing the inputs
    document.getElementById('loader').style.display = 'flex';
    document.getElementById('additional-fields').style.display = 'none';

    // Collect all input values as key-value pairs
    const additionalInputs = {};
    inputs.forEach(input => {
        additionalInputs[input.name] = input.value.trim();
    });

    // Get the original form values
    const subject = document.getElementById('subject').value;
    const platform = document.getElementById('platform').value;
    const tone = document.getElementById('tone').value;
    const includeHashtags = document.getElementById('hashtags').checked;
    const maxHashtags = includeHashtags ?
        parseInt(document.getElementById('maxHashtags').value) || 5 : 0;

    // Call the API again with all inputs
    fetch('/generate_with_inputs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            subject: subject,
            platform: platform,
            tone: tone,
            includeHashtags: includeHashtags,
            maxHashtags: maxHashtags,
            additionalInputs: additionalInputs,
            originalContent: originalContent
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
            // Display the final result
            document.getElementById('content-display').innerHTML = data.content.replace(/\n/g, '<br>');
            document.getElementById('result').style.display = 'block';
        }
    })
    .catch((error) => {
        // Hide loader
        document.getElementById('loader').style.display = 'none';

        // Show error
        document.getElementById('error').textContent = 'Failed to generate content with your inputs. Please try again.';
        document.getElementById('error').style.display = 'block';
        console.error('Error:', error);
    });
}