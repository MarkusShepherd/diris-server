package info.riemannhypothesis.dixit.server;

import java.text.SimpleDateFormat;

import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

// @EnableAutoConfiguration
@Configuration
@ComponentScan
@EnableWebMvc
// @Import(SocialConfig.class)
public class Application extends WebMvcConfigurerAdapter {

	public static final String GCS_BUCKET = "dixit";
	public static final SimpleDateFormat DATE_FORMATTER = new SimpleDateFormat(
			"yyyy-MM-dd'T'HH:mm:ss'Z'");

	// We do not have the typical main method because we need
	// the Maven AppEngine plugin to launch / configure the
	// development server. However, we are still using this
	// class to define configuration information.

}
