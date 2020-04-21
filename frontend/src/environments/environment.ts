/*
 * Ionic uses a configuration file to manage environment variables.
 * The below variables are required for user authentication.
 */

export const environment = {
  production: false,
  apiServerUrl: 'http://127.0.0.1:5000', // the running FLASK api server url
  auth0: {
    url: 'dev-sbac', // the auth0 domain prefix
    audience: 'coffeeshop', // the audience set for the auth0 app
    clientId: 'lLUvEZcRd1nKGM9wjRyiCKmjxO5OFfDu', // the client id generated for the auth0 app
    callbackURL: 'http://localhost:8100', // the base url of the running ionic application.
  }
};
