'use strict';

/*jslint browser: true */
/*global angular, console */

var app = {
    initialize: function initialize() {
        this.bindEvents();
    },
    bindEvents: function bindEvents() {
        document.addEventListener('deviceready', this.onDeviceReady, false);
    },
    onDeviceReady: function onDeviceReady() {
        app.receivedEvent('deviceready');
    },
    receivedEvent: function receivedEvent(id) {
        console.log('Received Event: ' + id);
        angular.bootstrap(document, ['dirisApp']);
    }
};

app.initialize();
