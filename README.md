# Dixit Server #

This is the backend to the [Dixit App](https://bitbucket.org/MarkusSchepke/dixitapp). To deploy it, clone the source and make sure you have `mvn` [installed](https://maven.apache.org/install.html).

Build the project by `mvn clean install`. Then you can run the test server with `mvn appengine:devserver`. Once you are happy with the results, you can deploy the project with `mvn appengine:update`. Read more about the build process with Maven [here](https://cloud.google.com/appengine/docs/java/tools/maven).