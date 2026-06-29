Build Job Application Tracker

You please read the file of B.L.A.S.T.md again and my objective again, and create a visually pleasing, lightweight React application which will track:


Job applications across multiple stages
Drag and drop cards between status columns
Theme switching (3-4 visual themes)
HR contact email attached to each job card


Columns required (in order):


Job Saved
Applied
In Progress
Follow-up
Interview
Offer
Rejected


Each job card should support:


Company name and role title
Notes / description field
Attached HR email (editable)
Attached resume/file reference (optional, as shown in reference image)
Date added / last updated timestamp
Edit and delete actions


Functional requirements:


Manual drag-and-drop between all columns
Add new job card via "+" on any column
Per-column count badges
Search/filter by company or role name
Sort by newest/oldest
Theme switcher offering at least 3-4 distinct visual themes (e.g. light, dark, pastel, high-contrast), persisted across sessions
Export/import board data (JSON)


UI/UX requirements:


Clean, modern board layout similar to the attached reference (Job Tracker AI)
Smooth drag interactions and hover states
Responsive layout for smaller screens
Empty-state placeholders ("No cards") per column
Name of the application should be : Job pathway

Additional good-to-have features:


Similar jobs recommendation: user picks a saved job card, app extracts role title and key skills/keywords from the notes, then generates pre-filled search links to LinkedIn Jobs, Naukri, Indeed, and Google Jobs (URL templates with query params, no scraping/API needed)
Application analytics dashboard: total applications, conversion rate per stage (e.g. Applied to Interview %), average time spent in each stage, busiest application week
Reminders/follow-up nudges: auto-flag cards that haven't moved in X days (e.g. "Applied 10 days ago, no update - consider following up"), shown as a badge or notification panel


You will be able to create the application based