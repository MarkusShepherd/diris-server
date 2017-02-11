dixitApp.controller('NewMatchController',
function($http, $location, $log, $rootScope, $scope, $timeout, toastr, dataService, BACKEND_URL) {

	var player = dataService.getLoggedInPlayer();

	if (!player) {
		$location.path('/login');
		return;
	}

	$scope.currentPlayer = player;
	$rootScope.menuItems = [{
		link: '#/overview',
		label: 'Overview',
		glyphicon: 'home'
	}];
	$rootScope.refreshPath = null;
	$rootScope.refreshReload = false;

	dataService.getPlayers()
	.then(function(players) {
		$scope.$apply(function () {
			$scope.players = players;
			$scope.playersArray = $.map(players, function(player) {
				return player;
			});
		});
	}).catch(function(response) {
		$log.debug('error');
		$log.debug(response);
		$scope.$apply(function () {
			toastr.error('There was an error fetching the data...');
		});
	});

	$scope.selected = {};
	$scope.numPlayers = 0;
	$scope.roundsPerPlayer = 2;

	$scope.addPlayer = function(p) {
		p.selected = true;
		$scope.selected["" + p.key.id] = p;
		$scope.numPlayers++;
	};

	$scope.removePlayer = function(p) {
		p.selected = false;
		delete $scope.selected["" + p.key.id];
		$scope.numPlayers--;
	};

	$scope.createMatch = function() {
		var playerIds = [];

		var includeCurrent = false;

		for (var pId in $scope.selected) {
			var id = parseInt(pId, 10);
			if (id == player.key.id) {
				includeCurrent = true;
				playerIds.unshift(id);
			} else
				playerIds.push(id);
		}

		if (!includeCurrent)
			playerIds.unshift(player.key.id);

		if (playerIds.length < 4) {
			toastr.error("Please select at least 3 players to invite to the match!");
			return;
		}

		$http.post(BACKEND_URL + '/match', playerIds)
		.then(function(response) {
			$log.debug(response);
			// TODO add response.data to dataService instead of force refresh below (#46)
			// TODO check a new match has been added
			$timeout(function() {
				$location.path('/overview/refresh');
			});
		}).catch(function(response) {
			$log.debug('error');
			$log.debug(response);
			$scope.$apply(function() {
				toastr.error("There was an error when creating the match...");
			});
		});
	}; // createMatch

}); // NewMatchController
