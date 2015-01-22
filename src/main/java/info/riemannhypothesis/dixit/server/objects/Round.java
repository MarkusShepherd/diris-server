package info.riemannhypothesis.dixit.server.objects;

public class Round {

    public enum Status {
        WAITING, SUBMIT_STORY, SUBMIT_OTHERS, SUBMIT_VOTES, FINISHED
    }

    private long    id;

    private long    matchId;

    private long    storyTellerId;
    private String  story;

    private Image[] images;

    private int[]   scores;

    private Status  status;

    private int[]   votes;

    public Round(Match match) {
        id = (long) (Math.random() * Long.MAX_VALUE);

        this.matchId = match.getId();
        int numPlayers = match.getPlayerIds().length;

        images = new Image[numPlayers];
        scores = new int[numPlayers];

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

    public boolean submissionComplete() {
        for (Image image : images) {
            if (image == null) {
                return false;
            }
        }
        return true;
    }

}
