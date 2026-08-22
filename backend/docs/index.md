# Welcome to the Tracksense Backend Documentation

There are three components to this system: the standalone app, the website, and the backend/database. The standalone app refers to the software that runs on the laptops that serve as detector stations for the radio signals. This software is also sometimes viewed directly by our sponsor through remote desktop login, so he can view information as it comes in. Meanwhile, the website is used by our sponsor and other users to access the aggregated information retrieved by the various detector stations, as well as add and verify additional information separately. This information is stored in the database and can be interacted with through the [API](./api/overview.md).

The standalone apps first receive radio signals from the radio detector attached to the laptops. It then processes those radio signals into binary, and then into usable information like train identification. The standalone app then both displays this information to anyone watching this detector station, and send the information to the backend API to be stored in the database.

The website has various basic functionality it needs to support, that ultimately allows users to interact with all of the data collected by the various detector stations/standalone apps. This includes:

- Retrieving data from the database using the API
- Allowing users to register for an account
- Allowing users to login and logout of their account
- Displaying data to users in a clear format
- Allowing volunteers to tag and verify data

## Work Done in 25/26

We received this project as a prototype, with a base tech stack decided for us by the previous team, unless we wanted to invest significant effort into changing it. That said, we did decide to look into switching out services used for the notification system and the email system. Our biggest constraint was simply being a team of very busy students, who could only afford to invest so many hours into a singular class. Furthermore, we encountered budget constraints while developing a project for an individual who aimed to keep costs minimal, opposed to a corporation with a larger budget. That meant that we were looking for free or low cost software for components like the notification system, or for potentially upgrading the map on the website to be interactive. Working on a project already in use, by both our sponsor and other users, meant that we had to be careful about testing our changes and modifying any server configuration to minimize the site downtime.

The current state of the product is a functional MVP that is in good shape to be expanded upon with new features in the future. We ended up having to reconsider our plan partway through the first semester, once we had access to the code base and handoff documentation. Our original plan, made when we only understood the basics of the project, was to jump into adding many features that our sponsor wanted like admin functionality on the website and ability to decode DPU signals. We also wanted to address some major issues like the broken notification system, as well as redesign the website UI. While DPU signals and alternatives to the current notification system service we researched, we were unable to do much to complete just about any of the rest of these initial goals.

Our second plan was created after we had gotten a chance to look through the code for the existing project. We found that before new features could be added, there were underlying issues with the backend code that needed to be addressed, or we’d just be pushing technical debt down the line and fighting with highly coupled code and a lack of tests the whole time. And so, we created our new plan in which we would prioritize refactoring the backend code to decouple the API from database queries and to minimize redundant code duplication. This aimed to increase the reliability and maintainability of the service, as well as to fix some of the bugs. Following this, we decided to create a suite of unit tests, since this was something lacking in the MVP. If we had additional time, we would then identify and address the high priority tasks from our original plan.

In the end, we refactored the backend, during which several major issues responsible for crashes and unreliability were resolved. Additionally, some unit tests were developed to cover the database layer and the new error handling system, which were essential features absent in the inital state of the project. We also fixed some bugs and improved the usability and security of a few of our services. Some of these changes were added to the plan as they were noticed or brought up as major issues. We also switched the site to use HTTPS rather than HTTP, improving the safety of user’s passwords.

## How to View/Serve the Documentation

We use `mkdocs` to generate Markdown and HTML files for our backend documentation. Most of the modules have documentation directly in the doc comments within the files themselves. For full documentation visit [mkdocs.org](https://www.mkdocs.org).

### Commands

* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

### Documentation layout

    backend
        mkdocs.yml    # The configuration file.
        ...
        docs/
            index.md  # The documentation homepage.
            ...       # Other markdown pages, images and other files.
