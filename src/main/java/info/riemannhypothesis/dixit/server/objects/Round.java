package info.riemannhypothesis.dixit.server.objects;

public class Round {

    public enum Status {
        WAITING, SUBMIT_STORY, SUBMIT_OTHERS, SUBMIT_VOTES, FINISHED
    }

    public static final int MAX_WRONG_VOTE_SCORE                       = 3;
    public static final int WRONG_VOTE_SCORE                           = 1;
    public static final int ALL_CORRECT_OR_WRONG_SCORE                 = 2;
    public static final int NOT_ALL_CORRECT_OR_WRONG_SCORE             = 3;
    public static final int NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE = 3;

    private long            id;

    private Match           match;
    private long            matchId;

    private long            storyTellerId;
    private int             storyTellerPos;
    private String          story;

    private Image[]         images;

    private int[]           scores;

    private Status          status;

    private int[]           votes;

    public Round(Match match) {
        id = (long) (Math.random() * Long.MAX_VALUE);

        this.match = match;
        this.matchId = match.getId();
        int numPlayers = match.getPlayerIds().length;

        images = new Image[numPlayers];
        scores = new int[numPlayers];
        votes = new int[numPlayers];

        for (int i = 0; i < votes.length; i++) {
            votes[i] = -1;
        }

        status = Status.WAITING;
    }

    public long getId() {
        return id;
    }

    public void setId(long id) {
        this.id = id;
    }

    public long getMatchId() {
        return matchId;
    }

    public void setMatchId(long matchId) {
        this.matchId = matchId;
    }

    public long getStoryTellerId() {
        return storyTellerId;
    }

    public void setStoryTellerId(long storyTellerId) {
        this.storyTellerId = storyTellerId;
        this.storyTellerPos = match.getPlayerPos(storyTellerId);
    }

    public String getStory() {
        return story;
    }

    public void setStory(String story) {
        this.story = story;
    }

    public Image[] getImages() {
        return images;
    }

    public void setImages(Image[] images) {
        this.images = images;
    }

    public int[] getScores() {
        return scores;
    }

    public void setScores(int[] scores) {
        this.scores = scores;
    }

    public Status getStatus() {
        return status;
    }

    public void setStatus(Status status) {
        this.status = status;
    }

    public int[] getVotes() {
        return votes;
    }

    public void setVotes(int[] votes) {
        this.votes = votes;
    }

    public int getImagePos(long id) {
        for (int i = 0; i < images.length; i++) {
            if (images[i].getId() == id) {
                return i;
            }
        }
        return -1;
    }

    public boolean submissionComplete() {
        for (Image image : images) {
            if (image == null) {
                return false;
            }
        }
        return true;
    }

    public boolean votesComplete() {
        for (int i = 0; i < votes.length; i++) {
            if (i != storyTellerPos && votes[i] < 0) {
                return false;
            }
        }
        return true;
    }

    public boolean calculateScores() {
        if (!(status == Status.SUBMIT_VOTES || status == Status.FINISHED)
                || !votesComplete()) {
            return false;
        }

        boolean allCorrect = true;
        boolean allWrong = true;

        int[] tempScores = new int[votes.length];

        for (int i = 0; i < votes.length; i++) {
            if (i == storyTellerPos)
                continue;

            if (votes[i] == storyTellerPos) {
                allWrong = false;
            } else {
                allCorrect = false;
                if (tempScores[votes[i]] < MAX_WRONG_VOTE_SCORE) {
                    tempScores[votes[i]] += WRONG_VOTE_SCORE;
                }
            }
        }

        if (allCorrect || allWrong) {
            for (int i = 0; i < votes.length; i++) {
                if (i != storyTellerPos)
                    tempScores[i] += ALL_CORRECT_OR_WRONG_SCORE;
            }
        } else {
            for (int i = 0; i < votes.length; i++) {
                if (i == storyTellerPos)
                    tempScores[i] += NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE;
                else if (votes[i] == storyTellerPos)
                    tempScores[i] += NOT_ALL_CORRECT_OR_WRONG_SCORE;
            }
        }

        scores = tempScores;
        status = Status.FINISHED;
        match.update();

        return true;
    }
}
