package info.riemannhypothesis.dixit.server.objects;

import java.util.HashMap;
import java.util.Map;

import javax.jdo.annotations.IdGeneratorStrategy;
import javax.jdo.annotations.PersistenceCapable;
import javax.jdo.annotations.Persistent;
import javax.jdo.annotations.PrimaryKey;

import lombok.Getter;
import lombok.Setter;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.google.appengine.api.datastore.Key;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
@Getter
@Setter
@PersistenceCapable
public class Round {

	public enum Status {
		WAITING, SUBMIT_STORY, SUBMIT_OTHERS, SUBMIT_VOTES, FINISHED
	}

	public static final int MAX_DECEIVED_VOTE_SCORE = 3;
	public static final int DECEIVED_VOTE_SCORE = 1;
	public static final int ALL_CORRECT_SCORE = 2;
	public static final int ALL_CORRECT_STORYTELLER_SCORE = 0;
	public static final int ALL_WRONG_SCORE = 2;
	public static final int ALL_WRONG_STORYTELLER_SCORE = 0;
	public static final int NOT_ALL_CORRECT_OR_WRONG_SCORE = 3;
	public static final int NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE = 3;

	@PrimaryKey
	@Persistent(valueStrategy = IdGeneratorStrategy.IDENTITY)
	private Key key;

	@JsonIgnore
	@Persistent
	private Match match;

	@Persistent
	private Key storyTellerKey;

	@Persistent
	private String story;

	@Persistent(serialized = "true", defaultFetchGroup = "true")
	private Map<Long, Long> images;

	@Persistent(serialized = "true", defaultFetchGroup = "true")
	private Map<Long, Long> imageToPlayer;

	@Persistent(serialized = "true", defaultFetchGroup = "true")
	private Map<Long, Integer> scores;

	@Persistent
	private Status status;

	@Persistent(serialized = "true", defaultFetchGroup = "true")
	private Map<Long, Long> votes;

	public Round(Match match) {
		this.match = match;
		images = new HashMap<Long, Long>();
		imageToPlayer = new HashMap<Long, Long>();
		scores = new HashMap<Long, Integer>();
		votes = new HashMap<Long, Long>();
		status = Status.WAITING;
	}

	public boolean submissionComplete() {
		if (status == Status.WAITING || status == Status.SUBMIT_STORY)
			return false;
		return images.size() == match.getPlayerKeys().size();
	}

	public boolean votesComplete() {
		if (status == Status.WAITING || status == Status.SUBMIT_STORY
				|| status == Status.SUBMIT_OTHERS)
			return false;
		return votes.size() == match.getPlayerKeys().size() - 1;
	}

	public boolean calculateScores() {
		if (!(status == Status.SUBMIT_VOTES || status == Status.FINISHED)
				|| !votesComplete())
			return false;

		boolean allCorrect = true;
		boolean allWrong = true;

		Map<Long, Integer> tempScores = new HashMap<Long, Integer>();

		for (long imageVoted : votes.values()) {
			long playerVoted = imageToPlayer.get(imageVoted);

			if (playerVoted == storyTellerKey.getId()) {
				allWrong = false;
			} else {
				allCorrect = false;
				Integer score = tempScores.get(playerVoted);
				if (score == null)
					score = 0;
				if (score < MAX_DECEIVED_VOTE_SCORE) {
					score += DECEIVED_VOTE_SCORE;
				}
				tempScores.put(playerVoted, score);
			}
		}

		if (allCorrect) {
			for (Key pKey : match.getPlayerKeys()) {
				Integer score = tempScores.get(pKey.getId());
				if (score == null)
					score = 0;
				if (pKey.equals(storyTellerKey))
					score += ALL_CORRECT_STORYTELLER_SCORE;
				else
					score += ALL_CORRECT_SCORE;
				tempScores.put(pKey.getId(), score);
			}
		} else if (allWrong) {
			for (Key pKey : match.getPlayerKeys()) {
				Integer score = tempScores.get(pKey.getId());
				if (score == null)
					score = 0;
				if (pKey.equals(storyTellerKey))
					score += ALL_WRONG_STORYTELLER_SCORE;
				else
					score += ALL_WRONG_SCORE;
				tempScores.put(pKey.getId(), score);
			}
		} else {
			Long storyTellerImage = images.get(storyTellerKey.getId());
			for (Key pKey : match.getPlayerKeys()) {
				Integer score = tempScores.get(pKey.getId());
				if (score == null)
					score = 0;
				if (pKey.equals(storyTellerKey))
					score += NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE;
				else if (storyTellerImage.equals(votes.get(pKey.getId())))
					score += NOT_ALL_CORRECT_OR_WRONG_SCORE;
				tempScores.put(pKey.getId(), score);
			}
		}

		scores = tempScores;
		status = Status.FINISHED;

		match.update();

		return true;
	}
}
