package info.riemannhypothesis.dixit.server.objects;

import info.riemannhypothesis.dixit.server.util.ListUtils;

import java.util.ArrayList;
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

    public static final int    STANDARD_TIMEOUT = 60 * 60 * 24; // 24h

    @PrimaryKey
    @Persistent(valueStrategy = IdGeneratorStrategy.IDENTITY)
    private Key                key;

    @Persistent
    private List<Key>          playerKeys;

    @Persistent(mappedBy = "match")
    private List<Round>        rounds;

    @Persistent
    private int                totalRounds;

    @Persistent
    private int                currentRound;

    @Persistent
    private Status             status;

    @Persistent(serialized = "true", defaultFetchGroup = "true")
    private Map<Long, Integer> standings;

    @Persistent
    private int                timeout;

    public Match(Set<Key> playerKeySet) {
        this(ListUtils.shuffledListFromSet(playerKeySet), playerKeySet.size(),
                STANDARD_TIMEOUT);
    }

    public Match(Set<Key> playerKeySet, int totalRounds) {
        this(ListUtils.shuffledListFromSet(playerKeySet), totalRounds,
                STANDARD_TIMEOUT);
    }

    public Match(Set<Key> playerKeySet, int totalRounds, int timeOut) {
        this(ListUtils.shuffledListFromSet(playerKeySet), totalRounds, timeOut);
    }

    public Match(List<Key> playerKeys) {
        this(playerKeys, playerKeys.size(), STANDARD_TIMEOUT);
    }

    public Match(List<Key> playerKeys, int totalRounds) {
        this(playerKeys, totalRounds, STANDARD_TIMEOUT);
    }

    public Match(List<Key> playerKeys, int totalRounds, int timeOut) {
        this.playerKeys = playerKeys;
        this.totalRounds = totalRounds;
        this.currentRound = 0;
        this.standings = new HashMap<Long, Integer>();
        this.timeout = timeOut;
        this.status = Status.IN_PROGRESS;

        this.rounds = new ArrayList<Round>(totalRounds);

        int numPlayers = playerKeys.size();
        for (int i = 0; i < totalRounds; i++) {
            Round round = new Round(this);

            int p = i % numPlayers;
            round.setStoryTellerKey(playerKeys.get(p));

            if (i == 0) {
                round.setStatus(Round.Status.SUBMIT_STORY);
            }

            rounds.add(round);
        }
    }

    public int getPlayerPos(Key pKey) {
        for (int i = 0; i < playerKeys.size(); i++) {
            if (playerKeys.get(i).equals(pKey)) {
                return i;
            }
        }
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

}
