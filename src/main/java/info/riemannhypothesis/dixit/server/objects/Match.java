package info.riemannhypothesis.dixit.server.objects;

import info.riemannhypothesis.dixit.server.Application;
import info.riemannhypothesis.dixit.server.util.Utils;

import java.text.ParseException;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;

import javax.jdo.annotations.IdGeneratorStrategy;
import javax.jdo.annotations.PersistenceCapable;
import javax.jdo.annotations.Persistent;
import javax.jdo.annotations.PrimaryKey;

import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.Setter;

import com.google.appengine.api.datastore.Key;
import com.google.appengine.api.datastore.KeyFactory;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
@Getter
@Setter
@EqualsAndHashCode(of = "key")
@PersistenceCapable
public class Match {

	public enum Status {
		WAITING, IN_PROGRESS, FINISHED
	}

	public static final int STANDARD_TIMEOUT = 60 * 60 * 24; // 24h

	@PrimaryKey
	@Persistent(valueStrategy = IdGeneratorStrategy.IDENTITY)
	private Key key;

	@Persistent
	private List<Key> playerKeys;

	@Persistent
	private Key invitingPlayer;

	@Persistent(serialized = "true", defaultFetchGroup = "true")
	private Map<Long, Boolean> accepted;

	@Persistent(mappedBy = "match")
	private List<Round> rounds;

	@Persistent
	private int totalRounds;

	@Persistent
	private int currentRound;

	@Persistent
	private Status status;

	@Persistent(serialized = "true", defaultFetchGroup = "true")
	private Map<Long, Integer> standings;

	@Persistent
	private int timeout;

	@Persistent
	private String created;
	@Persistent
	private String lastModified;

	public Match(Set<Key> playerKeySet, long pId) {
		this(Utils.shuffledListFromSet(playerKeySet), pId, playerKeySet.size(),
				STANDARD_TIMEOUT);
	}

	public Match(Set<Key> playerKeySet, long pId, int totalRounds) {
		this(Utils.shuffledListFromSet(playerKeySet), pId, totalRounds,
				STANDARD_TIMEOUT);
	}

	public Match(Set<Key> playerKeySet, long pId, int totalRounds, int timeOut) {
		this(Utils.shuffledListFromSet(playerKeySet), pId, totalRounds, timeOut);
	}

	public Match(List<Key> playerKeys, long pId) {
		this(playerKeys, pId, playerKeys.size(), STANDARD_TIMEOUT);
	}

	public Match(List<Key> playerKeys, long pId, int totalRounds) {
		this(playerKeys, pId, totalRounds, STANDARD_TIMEOUT);
	}

	public Match(List<Key> playerKeys, long pId, int totalRounds, int timeOut) {
		this.playerKeys = playerKeys;
		this.totalRounds = totalRounds;
		this.currentRound = 0;

		this.invitingPlayer = KeyFactory.createKey("Player", pId);
		this.accepted = new HashMap<Long, Boolean>();
		for (Key pKey : playerKeys)
			this.accepted.put(pKey.getId(), pKey.getId() == pId);

		this.standings = new HashMap<Long, Integer>();
		for (Key pKey : playerKeys)
			this.standings.put(pKey.getId(), 0);

		this.timeout = timeOut;
		this.status = Status.WAITING;

		this.rounds = new ArrayList<Round>(totalRounds);

		int numPlayers = playerKeys.size();
		for (int i = 0; i < totalRounds; i++) {
			Round round = new Round(this);

			int p = i % numPlayers;
			round.setStoryTellerKey(playerKeys.get(p));

			if (i == 0)
				round.setStatus(Round.Status.SUBMIT_STORY);

			rounds.add(round);
		}

		final String now = Utils.now();
		created = now;
		lastModified = now;
	}

	public int getPlayerPos(Key pKey) {
		for (int i = 0; i < playerKeys.size(); i++)
			if (playerKeys.get(i).equals(pKey))
				return i;
		return -1;
	}

	public int getPlayerPos(Player player) {
		return getPlayerPos(player.getKey());
	}

	public void update() {
		Map<Long, Integer> temp = new HashMap<Long, Integer>();

		for (Key pKey : playerKeys)
			temp.put(pKey.getId(), 0);

		boolean finished = true;

		for (int i = 0; i < rounds.size(); i++) {
			Round round = rounds.get(i);
			if (round.getStatus() == Round.Status.FINISHED) {
				for (Entry<Long, Integer> e : round.getScores().entrySet()) {
					Long pId = e.getKey();
					Integer score = temp.get(pId) + e.getValue();
					temp.put(pId, score);
				}
			} else {
				currentRound = i;
				if (round.getStatus() == Round.Status.WAITING)
					round.setStatus(Round.Status.SUBMIT_STORY);
				finished = false;
				break;
			}
		}

		if (finished)
			status = Status.FINISHED;

		standings = temp;
	}

	public Date getCreatedDate() {
		try {
			return Application.DATE_FORMATTER.parse(created);
		} catch (ParseException e) {
			e.printStackTrace(System.err);
			return null;
		}
	}

	public Date getLastModifiedDate() {
		try {
			return Application.DATE_FORMATTER.parse(lastModified);
		} catch (ParseException e) {
			e.printStackTrace(System.err);
			return null;
		}
	}

	public boolean accept(long pId) {
		if (status != Status.WAITING)
			return true;
		if (!accepted.containsKey(pId))
			throw new IllegalArgumentException("Player not found in match");
		accepted.put(pId, true);

		boolean allAccepted = true;
		for (boolean a : accepted.values())
			allAccepted = allAccepted && a;
		if (allAccepted)
			status = Status.IN_PROGRESS;
		return allAccepted;
	}
}
