package info.riemannhypothesis.dixit.server.controller;

import info.riemannhypothesis.dixit.server.client.MatchServiceApi;
import info.riemannhypothesis.dixit.server.objects.Image;
import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Player;
import info.riemannhypothesis.dixit.server.objects.Round;
import info.riemannhypothesis.dixit.server.repository.ImageRepository;
import info.riemannhypothesis.dixit.server.repository.JDOCrudRepository.Callback;
import info.riemannhypothesis.dixit.server.repository.MatchRepository;
import info.riemannhypothesis.dixit.server.repository.PlayerRepository;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Set;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;

import com.google.appengine.api.datastore.Key;
import com.google.appengine.api.datastore.KeyFactory;

/**
 * @author Markus Schepke
 * @date 16 Feb 2015
 */
@Controller
public class MatchService implements MatchServiceApi {

	@Autowired
	private MatchRepository matches;
	@Autowired
	private PlayerRepository players;
	@Autowired
	private ImageRepository images;

	@Override
	@RequestMapping(value = PATH, method = RequestMethod.POST, produces = "application/json")
	public @ResponseBody Match addMatch(@RequestBody List<Long> pIds) {
		Set<Key> pKeys = new HashSet<Key>();

		for (long pId : pIds) {
			pKeys.add(KeyFactory.createKey("Player", pId));
		}

		final Long invitingPlayer = pIds.get(0);
		Match match = new Match(pKeys, invitingPlayer);
		match = matches.save(match);

		final Key mKey = match.getKey();
		final Callback<Player> callback = new Callback<Player>() {
			@Override
			public void apply(Player player) {
				player.addMatch(mKey);
				if (player.getKey().getId() != invitingPlayer)
					try {
						player.sendPushNotification("New invitation",
								"You've been invited to a new match!");
					} catch (IOException e) {
						// TODO Auto-generated catch block
						e.printStackTrace();
					}
			}
		};

		for (Key pKey : pKeys) {
			players.update(pKey, callback);
		}

		return match;
	}

	@Override
	@RequestMapping(value = PATH, method = RequestMethod.GET, produces = "application/json")
	public @ResponseBody List<Match> getMatchList() {
		return matches.findAll();
	}

	@Override
	@RequestMapping(value = PATH + "/{id}", method = RequestMethod.GET, produces = "application/json")
	public @ResponseBody Match getMatch(@PathVariable("id") long id) {
		return matches.findById(KeyFactory.createKey("Match", id));
	}

	@Override
	@RequestMapping(value = PATH + "/{mId}/accept/{pId}", method = RequestMethod.POST, produces = "application/json")
	public @ResponseBody Match acceptMatch(@PathVariable("mId") long mId,
			@PathVariable("pId") final long pId) {
		Match match = getMatch(mId);

		if (match == null)
			throw new IllegalArgumentException("Match not found");
		if (match.getStatus() != Match.Status.WAITING)
			return null;

		Key playerKey = KeyFactory.createKey("Player", pId);
		List<Key> playerKeys = match.getPlayerKeys();
		if (!playerKeys.contains(playerKey))
			throw new IllegalArgumentException("Player not found in match");

		final Callback<Match> callback = new Callback<Match>() {
			@Override
			public void apply(Match match) {
				match.accept(pId);
			}
		};

		return matches.update(match.getKey(), callback);
	}

	@Override
	@RequestMapping(value = PATH + "/{id}/players", method = RequestMethod.GET, produces = "application/json")
	public @ResponseBody List<Player> getPlayers(@PathVariable("id") long id) {
		Match match = getMatch(id);
		if (match == null)
			return new LinkedList<Player>();
		return players.findByIds(match.getPlayerKeys());
	}

	@Override
	@RequestMapping(value = PATH + "/{id}/images", method = RequestMethod.GET, produces = "application/json")
	public @ResponseBody List<Image> getImages(@PathVariable("id") long id) {
		Match match = getMatch(id);
		if (match == null)
			return new LinkedList<Image>();

		List<Key> keys = new ArrayList<Key>();
		for (Round round : match.getRounds())
			for (long iId : round.getImages().values())
				keys.add(KeyFactory.createKey("Image", iId));

		final ArrayList<Image> list = new ArrayList<Image>(
				images.findByIds(keys));
		Collections.shuffle(list);
		return list;
	}

	@Override
	@RequestMapping(value = PATH + "/{id}/images/{rNo}", method = RequestMethod.GET, produces = "application/json")
	public @ResponseBody List<Image> getImages(@PathVariable("id") long id,
			@PathVariable("rNo") int rNo) {
		Match match = getMatch(id);
		if (match == null)
			return new LinkedList<Image>();

		List<Key> keys = new ArrayList<Key>();
		for (long iId : match.getRounds().get(rNo).getImages().values())
			keys.add(KeyFactory.createKey("Image", iId));

		final ArrayList<Image> list = new ArrayList<Image>(
				images.findByIds(keys));
		Collections.shuffle(list);
		return list;
	}

}
