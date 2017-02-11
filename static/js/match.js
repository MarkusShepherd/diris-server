dixitApp.controller('MatchController',
function($location, $log, $rootScope, $routeParams, $scope, blockUI, toastr, dataService) {

	var player = dataService.getLoggedInPlayer();

	if (!player) {
		$location.path('/login');
		return;
	}

	if (!blockUI.state().blocking)
		blockUI.start();

	$scope.currentPlayer = player;
	$rootScope.menuItems = [{
		link: '#/overview',
		label: 'Overview',
		glyphicon: 'home'
	}];

	var mId = $routeParams.mId;
	var action = $routeParams.action;

	$rootScope.refreshPath = '/match/' + mId + '/refresh';
	$rootScope.refreshReload = action === 'refresh';

	$scope.mId = mId;

	dataService.getMatch(mId, action === 'refresh')
	.then(function(match) {
		$scope.$apply(function() {
			$scope.match = processMatch(match, player);
		});
		return $scope.match;
	}).then(function(match) {
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
	}).catch(function(response) {
		$log.debug('error');
		$log.debug(response);
		$scope.$apply(function() {
			toastr.error("There was an error fetching the data - please try again later...");
			blockUI.stop();
		});
	});

	dataService.getImages(mId, undefined, true, true)
	.then(function(images) {
		$scope.$apply(function() {
			$scope.images = {};
			$.each(images, function(k, img) {
				$scope.images['' + img.key.id] = img;
			});
		});
		$log.debug('Images: ', $scope.images);
	}).catch(function(response) {
		$log.debug('error');
		$log.debug(response);
		$scope.$apply(function() {
			toastr.error("There was an error fetching the data - please try again later...");
		});
	});

}); // MatchController
