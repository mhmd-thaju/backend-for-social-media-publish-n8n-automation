For facebook page
- Create an app in facebook developers
- Go to App Settings >> Basic 
    - Give a privacy policy url
    - hit save changes
- Tools >> Graph api explorer
    - Select permissions for
        page_show_list
        pages_read_engagement
        pages_manage_posts
        pages_read_user_content
        page_events
        business_management
    - Generate access token
        in pop up select opt in to current and future pages
    - in the graph api expolrer search bar search me/accounts
        find the desired page and copy the access token 
    make a facebook graph api credential in n8n


for instagram
 - account should be professional account
 - go to facebook select the facebook page and link with the instagram account
 - go to business.facebook.com and locate the business portfolio of facebook page and instagram and go to select
 - ensure there is facebook page in pages section and instagram account in instagram account section
 - go to app  , create a new app , set up 
 - come back to app section and refresh the page to make sure the app is connected with business accout
 - go to system user click on add fill it up as employee
 - assign assets , full control on facebook pages, instagram and apps
 - generate token , select the app, expiration to never, permission to select
    business mangement
    instagram basic
    instagram content publish
    pages show list
    pages manage post 
    page read engagement
- generate access token and setup credential in the n8n


for LinkedIn
- create a page 
- go to linkedin developers
- add linkedin page and verify , also add logo
- go to products and add 
    Share on linkedin
    Sign in with linkedin using OpenID connect
    Events management API
- GO to Auth
- on the right click on OAuth 2.0 tools
- Create token
- select scopes and request access token
- go to n8n and setup linkedin credential while turning off legacy
