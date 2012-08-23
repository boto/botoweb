Welcome
=======

Welcome to the new home of botoweb, formerly known as boto_web. We have changed the name to botoweb to be more friendly and follow the PEP 8 guidelines for Package naming conventions, specifically:

    Package and Module Names

        Modules should have short, all-lowercase names.  Underscores can be used
        in the module name if it improves readability.  Python packages should
        also have short, all-lowercase names, although the use of underscores is
        discouraged.

This application has now been migrated to git and github, under the boto community.

Please feel free to contribute!

Check out the [Documentation](http://botoweb.readthedocs.org/)

Objective
==========

botoweb is an **Application Framework** for highly scalable application servers. It uses the standard [Three-Tier](http://en.wikipedia.org/wiki/Multitier_architecture#Three-tier_architecture) architecture to be housed in the [Amazon Web Services](http://aws.amazon.com/) environment. It uses [boto](http://code.google.com/p/boto) for communication with these services (hence the name, botoweb).

Installation
=============

 * [[Installing]]
 * [[Building|Building your first Application]]
 * [[Running|Running an Application Server]]
 * [[Shell|The botoweb shell environment]]
 * [[JSONEncoding|The JSON Encoding Specifics]]

Overview
========
botoweb uses wsgi and wsgi chaining to split the logic between multiple layers built inside of the framework:

 * Application Layer
 * Caching Layer
 * Filter Layer
 * Authentication Layer
 * Shared Resources
