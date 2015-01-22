package info.riemannhypothesis.dixit.server.objects;

import info.riemannhypothesis.dixit.server.objects.Round.Status;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public class Match {

    public static final int STANDARD_TIMEOUT = 60 * 60 * 24; // 24h

    private long            id;

    private long[]          playerIds;
    private Round[]         rounds;

    private int             totalRounds;
    private int             currentRound;

    private int[]           standings;

    private int             timeout;

    public Match() {
        id = 0;
    }

    public Match(long[] players) {
        this();
        this.playerIds = players;
        totalRounds = players.length;
        currentRound = 0;
        rounds = new Round[totalRounds];
        standings = new int[players.length];
        timeout = STANDARD_TIMEOUT;

        int numPlayers = players.length;
        for (int i = 0; i < rounds.length; i++) {
            int p = i % numPlayers;
            Round round = new Round(this);
            round.setStoryTellerId(playerIds[p]);
            rounds[i] = round;
        }
        rounds[0].setStatus(Status.SUBMIT_STORY);
    }

    public long getId() {
        return id;
    }

    public void setId(long id) {
        this.id = id;
    }

    public long[] getPlayerIds() {
        return playerIds;
    }

    public void setPlayerIds(long[] players) {
        this.playerIds = players;
    }

    public Round[] getRounds() {
        return rounds;
    }

    public void setRounds(Round[] rounds) {
        this.rounds = rounds;
    }

    public int getTotalRounds() {
        return totalRounds;
    }

    public void setTotalRounds(int totalRounds) {
        this.totalRounds = totalRounds;
    }

    public int getCurrentRound() {
        return currentRound;
    }

    public void setCurrentRound(int currentRound) {
        this.currentRound = currentRound;
    }

    public int[] getStandings() {
        return standings;
    }

    public void setStandings(int[] standings) {
        this.standings = standings;
    }

    public int getTimeout() {
        return timeout;
    }

    public void setTimeout(int timeout) {
        this.timeout = timeout;
    }

    public int getPlayerPos(long id) {
        for (int i = 0; i < playerIds.length; i++) {
            if (playerIds[i] == id) {
                return i;
            }
        }
        return -1;
    }

    public int getPlayerPos(Player player) {
        return getPlayerPos(player.getId());
    }
}
