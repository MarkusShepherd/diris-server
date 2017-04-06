'use strict';

dirisApp.controller('SubmitImageController', function SubmitImageController(
    $location,
    $log,
    $q,
    $rootScope,
    $routeParams,
    $scope,
    $timeout,
    blockUI,
    toastr,
    dataService
) {
    function getImage(srcType) {
        navigator.camera.getPicture(setImage, function (message) {
            $scope.$apply(function () {
                toastr.error(message);
            });
        }, {
            quality : 100,
            destinationType : Camera.DestinationType.DATA_URL,
            sourceType : srcType,
            encodingType: 0
        });
    }

    function setImage(imageData, isUrl) {
        $scope.$apply(function () {
            $scope.imageData = imageData;
            $scope.selectedImage = true;
            $("#image")
                .cropper('replace', isUrl ? imageData : "data:image/jpeg;base64," + imageData)
                .cropper('enable');
        });
    }

    var player = dataService.getLoggedInPlayer(),
        mPk = $routeParams.mPk,
        rNo = $routeParams.rNo,
        matchPromise,
        imagePromise;

    if (!player) {
        $location.path('/login');
        return;
    }

    if (!blockUI.state().blocking) {
        blockUI.start();
    }

    $scope.mPk = mPk;
    $scope.rNo = rNo;

    $scope.currentPlayer = player;
    $rootScope.menuItems = [{
        link: '#/overview',
        label: 'Overview',
        glyphicon: 'home'
    }, {
        link: '#/match/' + mPk,
        label: 'Match',
        glyphicon: 'knight'
    }];
    $rootScope.refreshPath = null;
    $rootScope.refreshReload = false;

    matchPromise = dataService.getMatch(mPk)
        .then(function (match) {
            $scope.match = match;
            $scope.round = match.rounds[rNo - 1];

            if ($scope.round.status === 'v') {
                $location.path('/vote/' + mPk + '/' + rNo).replace();
                return;
            }

            if ($scope.round.status === 'f') {
                $location.path('/review/' + mPk + '/' + rNo).replace();
                return;
            }

            return $q.all(_.map(match.players, function (pk) {
                return dataService.getPlayer(pk, false);
            }));
        }).then(function (players) {
            $scope.players = {};

            _.forEach(players || [], function (player) {
                $scope.players[player.pk] = player;
            });

            if ($scope.round.details.image) {
                return dataService.getImage($scope.round.details.image);
            }
        }).then(function (image) {
            blockUI.stop();

            if (image) {
                $scope.image = image;
                return [];
            } else {
                return dataService.getRandomImages(10);
            }
        }).then(function (images) {
            $scope.randomImages = images;
        }).then(function () {
            if (!$scope.randomImages) {
                return;
            }

            var $frame = $('#centered'),
                $wrap  = $frame.parent();

            $frame.sly({
                horizontal: 1,
                itemNav: 'centered',
                smart: 1,
                activateOn: 'click',
                mouseDragging: 1,
                touchDragging: 1,
                releaseSwing: 1,
                startAt: 0,
                scrollBar: $wrap.find('.scrollbar'),
                scrollBy: 1,
                speed: 300,
                elasticBounds: 1,
                // easing: 'easeOutExpo',
                dragHandle: 1,
                dynamicHandle: 1,
                clickBar: 1,
                prev: $wrap.find('.prev'),
                next: $wrap.find('.next')
            });

            $frame.sly('reload');

            // TODO hacky - there must be a better way!
            $timeout(function () {
                $frame.sly('reload');
            }, 1000);

            $(window).resize(function () {
                $frame.sly('reload');
            });
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error("There was an error fetching the data - please try again later...");
        }).then(blockUI.stop);

    $scope.hasCamera = !isBrowser();

    $scope.setGalleryImage = function setGalleryImage(image) {
        // setImage(image.file, true);
        $scope.imageData = image.file;
        $scope.selectedImage = true;
        $("#image")
            .cropper('replace', image.file)
            .cropper('enable');
    }

    $scope.getImageFromCamera = function getImageFromCamera() {
        getImage(Camera.PictureSourceType.CAMERA);
    };

    $scope.getImageFromLibrary = function getImageFromLibrary() {
        if (isBrowser()) {
            $('#file-input').trigger('click');
        } else {
            getImage(Camera.PictureSourceType.PHOTOLIBRARY);
        }
    };

    $scope.submitImage = function submitImage() {
        blockUI.start();
        $q(function (resolve) {
            $("#image").cropper('getCroppedCanvas', {
                width: 1080,
                height: 1080
            }).toBlob(resolve, 'image/jpeg', 0.5);
        }).then(function (image) {
            $log.debug(image);
            return dataService.submitImage(mPk, rNo, image, $scope.round.story);
        }).then(function (match) {
            $log.debug(match);
            $location.path('/match/' + mPk + '/refresh').replace();
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            blockUI.stop();
            toastr.error("There was an error");
        });
    };

    $scope.zoom = function zoom(ratio) {
        $('#image').cropper('zoom', ratio);
    };

    $scope.rotate = function rotate(angle) {
        $('#image').cropper('rotate', angle);
    };

    $scope.flip = function flip(axis) {
        var  img = $('#image');
        img.cropper('scale' + axis, -img.cropper('getData')['scale' + axis]);
    };

    $("#image").cropper({
        viewMode: 3,
        aspectRatio: 1,
        dragMode: 'move',
        modal: false,
        guides: false,
        center: false,
        highlight: false,
        autoCropArea: 1,
        cropBoxMovable: false,
        cropBoxResizable: false,
        toggleDragModeOnDblclick: false
    }).cropper('disable');

    $("#file-input").change(function () {
        if (this.files && this.files[0]) {
            var reader = new FileReader();

            reader.onload = function (e) {
                var d = e.target.result;
                setImage(d.substr(d.indexOf(",") + 1));
            };

            reader.readAsDataURL(this.files[0]);
        }
    });

});
