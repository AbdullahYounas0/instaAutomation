# Spintax Examples for DM Automation

This file contains examples of how to use spintax syntax in your custom DM prompts for maximum message variation.

## Basic Spintax Syntax
Use curly braces and pipe symbols to create variations:
`{option1|option2|option3}`

## Simple Examples

### Greetings
```
{Hello|Hi|Hey|Good day} {first_name}!
```
Generates: "Hello John!", "Hi John!", "Hey John!", "Good day John!"

### Service Introduction
```
I {provide|offer|deliver|specialize in} {virtual assistant services|VA support|business assistance|administrative help}.
```

### Call to Action
```
{Would you be interested?|Let's connect!|Worth a quick chat?|Interested in learning more?}
```

## Advanced Nested Spintax

### Time-Sensitive Greetings
```
{Good {morning|afternoon|evening}|Hello|Hi} {first_name}!
```
Generates: "Good morning John!", "Good afternoon John!", "Hello John!", etc.

### Complex Service Descriptions
```
I {help|assist|support} {business owners|entrepreneurs|professionals} {save time|increase productivity|streamline operations} through {professional VA services|comprehensive business support|tailored administrative assistance}.
```

## Complete Message Templates

### Professional Template
```
{Hello|Hi|Good day} {first_name}! 

I {noticed|saw|came across} your {profile|work|business|page} and {thought|figured|believed} you might {be interested in|benefit from|find value in} {virtual assistant services|professional VA support|business assistance|administrative help}.

I {help|assist|support|work with} {entrepreneurs|business owners|professionals|growing companies} {save valuable time|increase productivity|streamline operations|focus on growth} by {handling daily tasks|managing administrative work|providing comprehensive support|taking care of routine operations}.

{Would love to connect|Interested in learning more|Worth a quick conversation|Let's discuss how I can help}!
```

### Casual Template
```
{Hey|Hi there|Hello} {first_name}! 

{Hope you're doing well|Trust you're having a great day}! I {provide|offer|specialize in} {VA services|virtual assistance|business support} that {could help|might benefit|would support} {busy entrepreneurs|growing businesses|ambitious professionals} like yourself.

{This could save you|You could gain|This might free up} {significant time|valuable hours|10+ hours weekly} to {focus on what matters most|concentrate on growth|work on core business activities}.

{Interested in hearing more|Want to learn more|Worth a quick chat|Let's connect}?
```

### Question-Based Template
```
{Hi|Hello|Hey} {first_name}! 

Are you {struggling with daily admin tasks|looking for ways to save time|wanting to focus more on core business|needing help with routine operations}? 

I {specialize in|excel at|focus on} {helping|supporting|assisting} {entrepreneurs|business owners|professionals} like yourself {streamline operations|increase efficiency|save valuable time|boost productivity} through {comprehensive VA services|professional virtual assistance|tailored business support}.

{This could be exactly what you need|Worth exploring together|Interested in discussing|Let's chat about it}!
```

## Location-Based Variations

### Local Connection
```
{Hey|Hello|Hi} {first_name}! 

{Fellow {city} entrepreneur here|Connecting with {city} business owners|Reaching out to professionals in {city}}! 

I {provide|offer|deliver} {specialized VA services|comprehensive business support|professional virtual assistance} to {local businesses|area entrepreneurs|regional companies} and {thought|figured} you might be interested.

{Let's connect|Worth discussing|Interested in learning more|Could we chat}?
```

## Industry-Specific Spintax

### For E-commerce
```
I {help|assist|support} {e-commerce businesses|online stores|digital entrepreneurs} with {inventory management|customer service|order processing|administrative tasks} so you can {focus on growth|scale your business|concentrate on marketing|develop new products}.
```

### For Consultants
```
I {support|assist|help} {consultants|professional service providers|advisors} {manage client communications|handle scheduling|organize documentation|streamline administrative tasks} to {free up more billable hours|increase client capacity|improve efficiency|focus on core expertise}.
```

### For Real Estate
```
I {help|assist|support} {real estate professionals|property agents|realtors} with {lead management|client follow-ups|listing coordination|administrative tasks} so you can {close more deals|focus on client relationships|expand your business|increase sales}.
```

## Dynamic Placeholder Integration

These placeholders are automatically filled by the system:
- `{first_name}` - Target user's first name
- `{city}` - Target user's city
- `{bio}` - Target user's bio/description
- `{day_of_week}` - Current day (Monday, Tuesday, etc.)
- `{time_of_day}` - Current time context (morning, afternoon, evening)
- `{season}` - Current season
- `{compliment}` - Random professional compliment
- `{business_benefit}` - Random business benefit
- `{time_saver}` - Random time-saving reference

### Example with Placeholders
```
{Good {day_of_time}|Hello} {first_name}! 

I {noticed|saw} your {compliment} and {thought|figured} a {business_benefit} like {time_saver} might be valuable for your {bio} work in {city}.

I {specialize in|excel at} {helping|supporting} {professionals|entrepreneurs} like yourself with {virtual assistant services|comprehensive business support}.

{This {season}|Today|This {day_of_week}} {would be perfect|could be ideal} to {discuss this|explore opportunities|connect and chat}!
```

## Best Practices

### 1. Balance Variation with Quality
- Don't sacrifice message quality for variation
- Ensure all spintax options make grammatical sense
- Test your spintax patterns before using them

### 2. Maintain Consistency in Tone
- Keep all variations within the same professional level
- Ensure personality remains consistent across options
- Match the formality level throughout the message

### 3. Avoid Over-Spinning
- Don't spin every single word - it becomes unnatural
- Focus on key elements: greetings, services, benefits, CTAs
- Keep some elements consistent for brand recognition

### 4. Test Your Spintax
- Use the test script to verify your spintax works correctly
- Check that all combinations make sense
- Ensure no grammatical errors in any variation

## Pro Tips

1. **Nested Spintax**: Use sparingly - too much nesting can create weird combinations
2. **Contextual Variations**: Make sure all options fit the context
3. **Length Control**: Keep variation options similar in length to maintain message flow
4. **Grammar Check**: All spintax options should work grammatically in the sentence
5. **Brand Voice**: Maintain consistent brand personality across all variations

This spintax system helps create thousands of unique message variations while maintaining personalization and professional quality!
