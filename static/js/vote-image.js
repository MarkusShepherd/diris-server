dixitApp.controller('VoteImageController',
function($http, $location, $log, $rootScope, $routeParams, $scope, $timeout, blockUI, toastr, dataService, BACKEND_URL) {

	var player = dataService.getLoggedInPlayer();

	if (!player) {
		$location.path('/login');
		return;
	}

	if (!blockUI.state().blocking)
		blockUI.start();

	var mId = $routeParams.mId;
	var rNo = $routeParams.rNo;

	$scope.mId = mId;
	$scope.rNo = rNo;

	$scope.currentPlayer = player;
	$rootScope.menuItems = [{
		link: '#/overview',
		label: 'Overview',
		glyphicon: 'home'
	}, {
		link: '#/match/' + mId,
		label: 'Match',
		glyphicon: 'knight'
	}];
	$rootScope.refreshPath = null;
	$rootScope.refreshReload = false;

	dataService.getMatch(mId)
	.then(function(match) {
		$scope.$apply(function() {
			$scope.match = processMatch(match, player);
			$scope.round = $scope.match.rounds[rNo];
		});
		return $scope.match;
	}).then(function(match) {
		if ($scope.round.status === 'SUBMIT_STORY' || $scope.round.status === 'SUBMIT_OTHERS')
			$timeout(function() { $location.path('/image/' + mId + '/' + rNo).replace(); });
		else if ($scope.round.status === 'FINISHED')
			$timeout(function() { $location.path('/review/' + mId + '/' + rNo).replace(); });
		else {
			var promises = $.map(match.playerKeys, function(key) {
				return dataService.getPlayer(key.id);
			});
			$scope.players = {};
			Promise.all(promises)
			.then(function(players) {
				$scope.$apply(function() {
					$.each(players, function(i, player) {
						$scope.players[player.key.id] = player;
					});
					blockUI.stop();
				});
			});
		}
	}).catch(function(response) {
		$log.debug('error');
		$log.debug(response);
		$scope.$apply(function() {
			toastr.error("There was an error fetching the data - please try again later...");
			blockUI.stop();
		});
	});

	dataService.getImages(mId, rNo)
	.then(function(images) {
		$scope.$apply(function() {
			$scope.images = {};
			$.each(images, function(k, img) {
				$scope.images['' + img.key.id] = img;
			});
		});
	}).catch(function(response) {
		$log.debug('error');
		$log.debug(response);
		$scope.$apply(function() {
			toastr.error("There was an error fetching the data - please try again later...");
		});
	});

	$scope.selectImage = function(image) {
		if ($scope.round.imageToPlayer[image.key.id] != player.key.id)
			$scope.selectedImage = image;
	};

	$scope.submitVote = function() {
		$http.get(BACKEND_URL + '/vote?player=' + 
			player.key.id + '&match=' + mId + '&round=' + $scope.rNo + '&image=' + $scope.selectedImage.key.id)
		.then(function(response) {
			if (response.data)
				$timeout(function() { $location.path('/match/' + mId + '/refresh').replace(); });
			else {
				$log.debug('error');
				$log.debug(response);
				$scope.$apply(function() {
					toastr.error("There was an error...");
				});
			}
		}).catch(function(response) {
			$log.debug('error');
			$log.debug(response);
			$scope.$apply(function() {
				toastr.error("There was an error");
			});
		});
	};

});
