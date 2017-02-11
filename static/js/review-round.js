dixitApp.controller('ReviewRoundController',
function($location, $log, $rootScope, $routeParams, $scope, $timeout, blockUI, toastr, dataService) {

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
		else if ($scope.round.status === 'SUBMIT_VOTE')
			$timeout(function() { $location.path('/vote/' + mId + '/' + rNo).replace(); });
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

	dataService.getImages(mId, rNo, true, true)
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

	$scope.filterValues = function(items, value) {
		var result = [];
		angular.forEach(items, function(v, k) {
	        if (v == value)
	        	result.push(k);
	    });
	    return result;
	};

	$scope.filterOutKey = function(items, key) {
		var result = [];
		angular.forEach(items, function(v, k) {
	        if (k != key)
	        	result.push(v);
	    });
	    return result;
	};

});
