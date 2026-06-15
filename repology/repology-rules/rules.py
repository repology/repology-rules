import re

# ... existing code ...

# Add a new rule to handle the js-beautify collision
rules.append(
    {
        'name': 'js-beautify',
        'match': re.compile(r'^js-beautify$'),
        'replace': 'js-beautify-js',
        'comment': 'Rename js-beautify to js-beautify-js to avoid collision with jsbeautifier',
    }
)

rules.append(
    {
        'name': 'jsbeautifier',
        'match': re.compile(r'^jsbeautifier$'),
        'replace': 'js-beautify-py',
        'comment': 'Rename jsbeautifier to js-beautify-py to avoid collision with js-beautify',
    }
)

# ... existing code ...
