package info.riemannhypothesis.dixit.server.repository;

import info.riemannhypothesis.dixit.server.objects.Player;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.springframework.stereotype.Service;

import com.google.android.gcm.server.Result;
import com.google.appengine.api.datastore.Key;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
@Service
public class PlayerRepository extends JDOCrudRepository<Player, Key> {

	public PlayerRepository() {
		super(Player.class);
	}

	public List<Result> sendPushNotifications(String title, String message,
			Iterable<Key> pKeys) {
		return sendPushNotifications(title, message, pKeys, new HashSet<Key>());
	}

	public List<Result> sendPushNotifications(String title, String message,
			Iterable<Key> pKeys, Key except) {
		Set<Key> set = new HashSet<Key>();
		set.add(except);
		return sendPushNotifications(title, message, pKeys, set);
	}

	public List<Result> sendPushNotifications(String title, String message,
			Iterable<Key> pKeys, Set<Key> except) {
		List<Result> list = new ArrayList<Result>();
		for (Key pKey : pKeys) {
			if (except != null && except.contains(pKey))
				continue;
			Player player = findById(pKey);
			try {
				list.add(player.sendPushNotification(title, message));
			} catch (IOException e) {
				e.printStackTrace();
			}
		}

		return list;
	}
}
