'use strict';

/*jslint browser: true, nomen: true */
/*global _, dirisApp, utils */

dirisApp.controller('FooterController', function FooterController(
    $scope,
    $window,
    ANDROID_APP_LINK,
    CREATOR_LINK,
    CREATOR_NAME,
    FEEDBACK_EMAIL,
    FEEDBACK_LINK
) {
    $scope.now = _.now();
    $scope.appLink = utils.isAndroid() ? ANDROID_APP_LINK : null; // && utils.isBrowser()
    $scope.creatorName = CREATOR_NAME;
    $scope.creatorLink = CREATOR_LINK;
    $scope.feedbackEmail = FEEDBACK_EMAIL;
    $scope.feedbackLink = FEEDBACK_LINK;

    $scope.open = function open(url) {
        if (url) {
            $window.open(url, '_system', 'location=yes');
        }
    };
});
