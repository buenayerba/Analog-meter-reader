import javafx.application.Application;
import javafx.beans.value.ChangeListener;
import javafx.beans.value.ObservableValue;
import javafx.collections.FXCollections;
import javafx.concurrent.Task;
import javafx.embed.swing.SwingFXUtils;
import javafx.event.ActionEvent;
import javafx.event.EventHandler;
import javafx.scene.Node;
import javafx.scene.Scene;
import javafx.scene.SnapshotParameters;
import javafx.scene.control.*;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TextField;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.image.PixelWriter;
import javafx.scene.image.WritableImage;
import javafx.scene.input.KeyCode;
import javafx.scene.input.MouseEvent;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Pane;
import javafx.scene.layout.VBox;
import javafx.scene.paint.Color;
import javafx.scene.shape.Circle;
import javafx.scene.text.Font;
import javafx.scene.text.FontWeight;
import javafx.stage.FileChooser;
import javafx.stage.Stage;
import javafx.scene.Group;
import javax.imageio.ImageIO;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import java.awt.image.RenderedImage;
import java.sql.Timestamp;
import java.text.SimpleDateFormat;
import javafx.scene.image.WritableImage;
import java.util.Date;

import javafx.geometry.Insets;
import java.awt.*;
import java.io.*;
import java.net.MalformedURLException;
import java.util.ArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.shape.Rectangle;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

/*
 * Allow user to choose an image to display,
 * and identify key points for reading the meter
 */

public class ProcessImage extends Application {

    String imagePath = "images/";
    ImageView imageView_original = new ImageView();
    ImageView imageView_edit = new ImageView();
    ImageView imageView_coord = new ImageView();
    ArrayList<Point> points = new ArrayList<Point>();
    ArrayList<Point> selection = new ArrayList<Point>();
    int FLAG = 0; // for deciding whether to capture mouse coordinates or not in scene2
    int FLAG2 = 0; // for deciding whether to capture mouse coordinates or not in scene3
    int SHAPE = 0; // 0 - rectangle, 1 - oval for the whole meter, 2 - circles for each dial
    public final int WIDTH = 960;
    public final int HEIGHT = 720;
    public final int LINE_WIDTH1 = 10;
    public final int LINE_WIDTH2 = 5;
    public int count = 0;
    public int count1 = 0;

    Circle c = new Circle();
    Rectangle r = new Rectangle();
    Image image;
    Image[] imgs = {null};
    String path = "";
    String path_original = "";
    String path_original_temp = "";
    String path_original_relative = "";
    boolean hasSavedOriginal = false;
    int type = 1;
    float angle = 0;
    int num_dials = 0;
    int orien = 1;
    float ulx = 0;
    float uly = 0;
    float blx = 0;
    float bly = 0;
    float urx = 0;
    float ury = 0;
    float brx = 0;
    float bry = 0;
    int left = 0;
    int right = 0;
    int bottom_dial_type = 1;
    int time_interval = 60;
    String filename_tosave = "";
    private static final SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd-HH-mm-ss");


    @Override
    public void start(Stage stage) throws FileNotFoundException {

        // ================================================== Scene 1 ==================================================
        Button select_image = new Button("Select an image");
        select_image.setPrefWidth(300);
        select_image.setPrefHeight(50);
        select_image.setLayoutX(50);
        select_image.setLayoutY(80);
        select_image.setFont(Font.font("Arial", FontWeight.BOLD, 22));

        Label selected_label = new Label("No image file is selected");
        selected_label.setPrefWidth(240);
        selected_label.setPrefHeight(10);
        selected_label.setLayoutX(120);
        selected_label.setLayoutY(150);

        Button continue_1 = new Button("Continue");
        continue_1.setPrefWidth(120);
        continue_1.setPrefHeight(10);
        continue_1.setLayoutX(140);
        continue_1.setLayoutY(190);

        select_image.setOnAction(event -> {
            FileChooser fileChooser = new FileChooser();
            fileChooser.setTitle("Open Resource Image File");
            File selectedFile = fileChooser.showOpenDialog(stage);
            if (selectedFile != null) {
                try {
                    openFile(selectedFile);
                } catch (MalformedURLException e) {
                    e.printStackTrace();
                }
                path_original_temp = selectedFile.getPath();
                String[] tokens = selectedFile.getPath().split("/");
                String relativePath = "";
                for (String t : tokens)
                    relativePath = t;
                Timestamp timestamp = new Timestamp(System.currentTimeMillis());
                path_original = path_original_temp.replaceAll(relativePath, "original_" + sdf.format(timestamp) + ".jpeg");
                path_original_relative = "original_" + sdf.format(timestamp) + ".jpeg";
                selected_label.setText(relativePath + "  selected");
            }
        });

        // Create group1
        Group group1 = new Group();
        group1.getChildren().add(select_image);
        group1.getChildren().add(continue_1);
        group1.getChildren().add(selected_label);
        Scene scene1 = new Scene(group1, 400, 300);

        // ================================================== Scene 2 ==================================================

        Canvas canvas = new Canvas(WIDTH, HEIGHT);
        GraphicsContext gc = canvas.getGraphicsContext2D();
        Canvas canvas_for_mask = new Canvas(WIDTH, HEIGHT);
        GraphicsContext gc_for_mask = canvas_for_mask.getGraphicsContext2D();
        gc_for_mask.setFill(Color.BLACK);
        gc_for_mask.fillRect(0,0,WIDTH,HEIGHT);

        imageView_edit.setLayoutX(0);
        imageView_edit.setLayoutY(0);

        // title
        Label title_3 = new Label("Identify general areas and annotate circular dials");
        title_3.setFont(Font.font("Arial", FontWeight.BOLD, 18));
        title_3.setLayoutX(300);
        title_3.setLayoutY(750);

        Label instruction1 = new Label("Please select your action: ");
        instruction1.setPrefWidth(250);
        instruction1.setPrefHeight(10);
        instruction1.setLayoutX(50);
        instruction1.setLayoutY(865);
        instruction1.setFont(Font.font("Arial", 16));

        // Button to save image
        Button save_edited = new Button("Save");
        save_edited.setPrefWidth(120);
        save_edited.setPrefHeight(30);
        save_edited.setLayoutX(300);
        save_edited.setLayoutY(860);

        // Button to clear drawing
        Button clear = new Button("Clear");
        clear.setPrefWidth(120);
        clear.setPrefHeight(30);
        clear.setLayoutX(450);
        clear.setLayoutY(860);

        // Button to continue to next page
        Button continue_3 = new Button("Continue");
        continue_3.setPrefWidth(120);
        continue_3.setPrefHeight(30);
        continue_3.setLayoutX(600);
        continue_3.setLayoutY(860);

        Label instruction2 = new Label("Please select the shape to draw: ");
        instruction2.setPrefWidth(250);
        instruction2.setPrefHeight(10);
        instruction2.setLayoutX(50);
        instruction2.setLayoutY(805);
        instruction2.setFont(Font.font("Arial", 16));

        // Button to select drawing shape: rectangle
        Button buttonR = new Button("Rectangle");
        buttonR.setPrefWidth(120);
        buttonR.setPrefHeight(30);
        buttonR.setLayoutX(300);
        buttonR.setLayoutY(800);
        buttonR.setStyle("-fx-text-fill: #048BB5");

        // Button to select drawing shape: oval
        Button buttonO = new Button("Circle");
        buttonO.setPrefWidth(120);
        buttonO.setPrefHeight(30);
        buttonO.setLayoutX(450);
        buttonO.setLayoutY(800);
        buttonO.setStyle("-fx-text-fill: #278119");

        // Button to select drawing shape: oval
        Button buttonS = new Button("Small Circle");
        buttonS.setPrefWidth(120);
        buttonS.setPrefHeight(30);
        buttonS.setLayoutX(600);
        buttonS.setLayoutY(800);
        buttonS.setStyle("-fx-text-fill: #e1990f");

        EventHandler<javafx.scene.input.MouseEvent> imageHandlerPressed = new EventHandler<javafx.scene.input.MouseEvent>() {
            @Override
            public void handle(javafx.scene.input.MouseEvent e) {
                if (FLAG == 1) {
                    if (SHAPE == 0) { // rectangle
                        r.setX(e.getX());
                        r.setY(e.getY());
                    } else if (SHAPE == 1 || SHAPE == 2) { // circle
                        c.setCenterX(e.getX());
                        c.setCenterY(e.getY());
                    }
                }
            }
        };

        EventHandler<javafx.scene.input.MouseEvent> imageHandlerReleased = new EventHandler<javafx.scene.input.MouseEvent>() {
            @Override
            public void handle(javafx.scene.input.MouseEvent e) {
                if (FLAG == 1) {
                    count++;
                    selection.add(new Point((int)e.getX(), (int)e.getY()));
                    if (SHAPE == 0) { // rectangle
                        r.setWidth(Math.abs((e.getX() - r.getX())));
                        r.setHeight(Math.abs((e.getY() - r.getY())));

                        // set different colors
                        if (count == 1) {
                            gc.setStroke(Color.WHITE);
                            gc_for_mask.setStroke(Color.WHITE);
                        }
                        else if (count == 2) {
                            gc.setStroke(Color.RED);
                            gc_for_mask.setStroke(Color.RED);
                        }
                        else if (count == 3) {
                            gc.setStroke(Color.BLUE);
                            gc_for_mask.setStroke(Color.BLUE);
                        }
                        else  {
                            gc.setStroke(Color.GREEN);
                            gc_for_mask.setStroke(Color.GREEN);
                        }

                        // set different line widths
                        if (count == 1) {
                            gc.setLineWidth(LINE_WIDTH1);
                            gc_for_mask.setLineWidth(LINE_WIDTH1);
                        }

                        else {
                            gc.setLineWidth(LINE_WIDTH2);
                            gc_for_mask.setLineWidth(LINE_WIDTH2);
                        }

                        gc.strokeRect(r.getX(), r.getY(), r.getWidth(), r.getHeight());
                        gc_for_mask.strokeRect(r.getX(), r.getY(), r.getWidth(), r.getHeight());
                        r = new Rectangle();
                    } else if (SHAPE == 1) { // circle
                        double xBound = c.getCenterX();
                        double yBound = c.getCenterY();
                        double diffX = Math.abs(e.getX() - c.getCenterX()); // c.getCenterX() is actually the X-coord of the upper left bound
                        double diffY = Math.abs(e.getY() - c.getCenterY()); // c.getCenterY() is actually the Y-coord of the upper left bound
                        c.setCenterX((xBound + e.getX()) / 2);
                        c.setCenterY((yBound + e.getY()) / 2);
                        c.setRadius((Math.sqrt(diffX * diffX + diffY * diffY))/2);

                        // set different colors
                        if (count == 1) {
                            gc.setStroke(Color.WHITE);
                            gc_for_mask.setStroke(Color.WHITE);
                        }
                        else if (count == 2) {
                            gc.setStroke(Color.RED);
                            gc_for_mask.setStroke(Color.WHITE);
                        }
                        else if (count == 3) {
                            gc.setStroke(Color.BLUE);
                            gc_for_mask.setStroke(Color.WHITE);
                        }
                        else  {
                            gc.setStroke(Color.GREEN);
                            gc_for_mask.setStroke(Color.WHITE);
                        }

                        // set different line widths
                        if (count == 1) {
                            gc.setLineWidth(LINE_WIDTH1);
                            gc_for_mask.setLineWidth(LINE_WIDTH1);
                        }
                        else {
                            gc.setLineWidth(LINE_WIDTH2);
                            gc_for_mask.setLineWidth(LINE_WIDTH2);
                        }

                        gc.strokeOval(c.getCenterX()-c.getRadius(), c.getCenterY()-c.getRadius(), c.getRadius()*2, c.getRadius()*2);
                        gc_for_mask.strokeOval(c.getCenterX()-c.getRadius(), c.getCenterY()-c.getRadius(), c.getRadius()*2, c.getRadius()*2);
                        c = new Circle();
                    } else if (SHAPE == 2) { // small circles for dials
                        num_dials++;
                        double xBound = c.getCenterX();
                        double yBound = c.getCenterY();
                        double diffX = Math.abs(e.getX() - c.getCenterX()); // c.getCenterX() is actually the X-coord of the upper left bound
                        double diffY = Math.abs(e.getY() - c.getCenterY()); // c.getCenterY() is actually the Y-coord of the upper left bound
                        c.setCenterX((xBound + e.getX()) / 2);
                        c.setCenterY((yBound + e.getY()) / 2);
                        c.setRadius((Math.sqrt(diffX * diffX + diffY * diffY))/2);
                        gc.setStroke(Color.YELLOW);
                        gc_for_mask.setStroke(Color.YELLOW);
                        gc.setLineWidth(LINE_WIDTH2);
                        gc_for_mask.setLineWidth(LINE_WIDTH2);
                        gc.strokeOval(c.getCenterX()-c.getRadius(), c.getCenterY()-c.getRadius(), c.getRadius()*2, c.getRadius()*2);
                        gc_for_mask.strokeOval(c.getCenterX()-c.getRadius(), c.getCenterY()-c.getRadius(), c.getRadius()*2, c.getRadius()*2);
                        c = new Circle();
                    }
                }
            }
        };
        imageView_edit.addEventHandler(MouseEvent.MOUSE_PRESSED, imageHandlerPressed);
        imageView_edit.addEventHandler(MouseEvent.MOUSE_RELEASED, imageHandlerReleased);
        canvas.addEventHandler(javafx.scene.input.MouseEvent.MOUSE_PRESSED, imageHandlerPressed);
        canvas.addEventHandler(javafx.scene.input.MouseEvent.MOUSE_RELEASED, imageHandlerReleased);

        // Create group3
        Group group3 = new Group();
        Pane pane3 = new Pane(); // for snapshot
        pane3.prefWidth(WIDTH);
        pane3.prefHeight(HEIGHT);
        pane3.getChildren().add(imageView_edit);
        pane3.getChildren().add(canvas);
        group3.getChildren().add(pane3);
        group3.getChildren().add(clear);
        group3.getChildren().add(continue_3);
        group3.getChildren().add(save_edited);
        group3.getChildren().add(buttonR);
        group3.getChildren().add(buttonO);
        group3.getChildren().add(buttonS);
        group3.getChildren().add(instruction1);
        group3.getChildren().add(instruction2);
        group3.getChildren().add(title_3);
        Scene modify_image_scene = new Scene(group3, 1000, 960);

        clear.setOnAction(event -> {
            gc.clearRect(0, 0, canvas.getWidth(), canvas.getHeight());
            gc_for_mask.clearRect(0, 0, canvas.getWidth(), canvas.getHeight());
            gc_for_mask.setFill(Color.BLACK);
            gc_for_mask.fillRect(0,0,WIDTH,HEIGHT);
            count = 0;
            num_dials = 0;
            title_3.setTextFill(Color.BLACK);
            title_3.setText("Identify general areas and annotate circular dials");
        });
        buttonR.setOnAction(event -> {
            if (!hasSavedOriginal) {
                saveFileAutomatic(path_original, pane3);
                hasSavedOriginal = true;
            }
            FLAG = 1;
            SHAPE = 0;
        });
        buttonO.setOnAction(event -> {
            if (!hasSavedOriginal) {
                saveFileAutomatic(path_original, pane3);
                hasSavedOriginal = true;
            }
            FLAG = 1;
            SHAPE = 1;
        });
        buttonS.setOnAction(event -> {
            if (!hasSavedOriginal) {
                saveFileAutomatic(path_original, pane3);
                hasSavedOriginal = true;
            }
            FLAG = 1;
            SHAPE = 2;
        });

        save_edited.setOnAction(event -> {
            // save the mask
            String maskName = "mask.jpeg";
            File maskImage     = new File(maskName);
            WritableImage writableImage = new WritableImage(WIDTH, HEIGHT);
            canvas_for_mask.snapshot(null, writableImage);
            RenderedImage renderedImage = SwingFXUtils.fromFXImage(writableImage, null);
            try {
                ImageIO.write(renderedImage, "png", maskImage);
            } catch (IOException e) {
                e.printStackTrace();
            }
            title_3.setTextFill(Color.BLUEVIOLET);
            title_3.setText("The mask is saved in the current directory.");
        });

//        save_edited.setOnAction(event -> {
//            FileChooser fileChooser = new FileChooser();
//            fileChooser.setTitle("Save the Edited Image");
//            File file = fileChooser.showSaveDialog(stage);
//            if (file != null) {
//                try {
//                    path = saveFile(file, pane3);
//
//                    // save the mask
//                    String maskName = "mask.jpeg";
//                    File maskImage     = new File(maskName);
//                    WritableImage writableImage = new WritableImage(WIDTH, HEIGHT);
//                    canvas_for_mask.snapshot(null, writableImage);
//                    RenderedImage renderedImage = SwingFXUtils.fromFXImage(writableImage, null);
//                    ImageIO.write(renderedImage, "png", maskImage);
//                } catch (MalformedURLException e) {
//                    e.printStackTrace();
//                } catch (IOException e) {
//                    e.printStackTrace();
//                }
//            }
//        });

        // ================================================== Scene 3 ==================================================

        Canvas canvas2 = new Canvas(WIDTH, HEIGHT);
        GraphicsContext gc2 = canvas2.getGraphicsContext2D();
        gc2.setStroke(Color.RED);
        gc2.setLineWidth(3);

        imageView_coord.setLayoutX(0);
        imageView_coord.setLayoutY(0);

        // title
        Label title_4 = new Label("Annotate main dial");
        title_4.setFont(Font.font("Arial", FontWeight.BOLD, 18));
        title_4.setLayoutX(400);
        title_4.setLayoutY(750);

        // Button to start selection
        Button startScene3 = new Button("Start");
        startScene3.setPrefWidth(120);
        startScene3.setPrefHeight(30);
        startScene3.setLayoutX(250);
        startScene3.setLayoutY(860);

        // Button to skip main dial identification
        Button skip = new Button("Skip");
        skip.setPrefWidth(120);
        skip.setPrefHeight(30);
        skip.setLayoutX(400);
        skip.setLayoutY(860);

        Button continue_4 = new Button("Continue");
        continue_4.setPrefWidth(120);
        continue_4.setPrefHeight(30);
        continue_4.setLayoutX(550);
        continue_4.setLayoutY(860);

        Label labelScene3 = new Label("Please click \"Start\" to select the corners of the bottom scale in this order: top-left, bottom-left, top-right");
        labelScene3.setPrefWidth(725);
        labelScene3.setPrefHeight(22);
        labelScene3.setLayoutX(80);
        labelScene3.setLayoutY(800);
        labelScene3.setFont(Font.font("Arial", 16));

        // For debug
        Label labelDeBugScene3 = new Label(" (x = "   +  0  +   " , y = "   +  0 + ")");
        labelDeBugScene3.setFont(Font.font("Arial", 16));
        labelDeBugScene3.setLayoutX(810);
        labelDeBugScene3.setLayoutY(800);

//        PrintStream fileOut2 = new PrintStream("output");
//        System.setOut(fileOut2);

        EventHandler<javafx.scene.input.MouseEvent> imageHandler2 = new EventHandler<javafx.scene.input.MouseEvent>() {
            @Override
            public void handle(javafx.scene.input.MouseEvent e) {
                float tempX = (float) e.getX();
                float tempY = (float) e.getY();
                if (FLAG2 == 1) {
                    count1++;
                    System.out.println(" (x = "   +  tempX +   " , y = "   +  tempY + ")");
                    labelDeBugScene3.setText(" (x = "   +  tempX   +   " , y = "   +  tempY + ")");
                    points.add(new Point((int)e.getX(), (int)e.getY()));
                }
                if (count1 == 1) {
                    ulx = tempX;
                    uly = tempY;
                    gc2.strokeOval(ulx-7, uly-7, 14, 14);
                }
                else if (count1 == 2) {
                    blx = tempX;
                    bly = tempY;
                    brx = blx;
                    bry = bly;
                    gc2.strokeOval(blx-7, bly-7, 14, 14);
                }
                else if (count1 == 3) {
                    urx = tempX;
                    ury = tempY;
                    gc2.strokeOval(urx-7, ury-7, 14, 14);
                }
            }
        };
        imageView_coord.addEventHandler(javafx.scene.input.MouseEvent.MOUSE_CLICKED, imageHandler2);
        canvas2.addEventHandler(javafx.scene.input.MouseEvent.MOUSE_CLICKED, imageHandler2);

        // Create group4
        Group group4 = new Group();
        Pane pane4 = new Pane(); // for snapshot
        pane4.prefWidth(WIDTH);
        pane4.prefHeight(HEIGHT);
        pane4.getChildren().add(imageView_coord);
        pane4.getChildren().add(canvas2);
        group4.getChildren().add(pane4);
        group4.getChildren().add(startScene3);
        group4.getChildren().add(skip);
        group4.getChildren().add(continue_4);
        group4.getChildren().add(title_4);
        group4.getChildren().add(labelScene3);
        group4.getChildren().add(labelDeBugScene3);
        Scene get_coord_scene = new Scene(group4, 1000, 960);

        startScene3.setOnAction(event -> {
            System.out.println("Coordinates of the bottom scale boundary points");
            FLAG2 = 1;
        });

        // ================================================ Scene 4 ================================================

        Label title_5 = new Label("Please fill in the information below and select \"Create XML\"");
        title_5.setFont(Font.font("Arial", FontWeight.BOLD, 18));
        title_5.setLayoutX(350);
        title_5.setLayoutY(20);

        final ToggleGroup tgroup1 = new ToggleGroup();
        HBox hb = new HBox();
        hb.setSpacing(10);
        Label type_label = new Label("Type of analog meter:");
        RadioButton rb1 = new RadioButton("Circular Dial Only");
        rb1.setToggleGroup(tgroup1);
        rb1.setSelected(true);
        RadioButton rb2 = new RadioButton("Main Dial Only");
        rb2.setToggleGroup(tgroup1);
        RadioButton rb3 = new RadioButton("Both");
        rb3.setToggleGroup(tgroup1);
        hb.getChildren().add(type_label);
        hb.getChildren().add(rb1);
        hb.getChildren().add(rb2);
        hb.getChildren().add(rb3);

        HBox hb1 = new HBox();
        hb1.setSpacing(10);
        Label base_angle_label = new Label("Base Angle:");
        TextField base_angle_text = new TextField ();
        base_angle_text.setText("0.0");
        hb1.getChildren().add(base_angle_label);
        hb1.getChildren().add(base_angle_text);
//        Button find_angle = new Button("Find base angle");
//        hb1.getChildren().add(find_angle);

        HBox hb2 = new HBox();
        hb2.setSpacing(10);
        Label num_dials_label = new Label("Number of circular Dials:");
        TextField num_dials_text = new TextField ();
        num_dials_text.setText("0");
        hb2.getChildren().add(num_dials_label);
        hb2.getChildren().add(num_dials_text);

        final ToggleGroup tgroup2 = new ToggleGroup();
        HBox hb3 = new HBox();
        hb3.setSpacing(10);
        Label orientation_label = new Label("Orientation of the leftmost dial:");
        RadioButton rb4 = new RadioButton("Clockwise");
        rb4.setToggleGroup(tgroup2);
        rb4.setSelected(true);
        RadioButton rb5 = new RadioButton("Counter-clockwise");
        rb5.setToggleGroup(tgroup2);
        hb3.getChildren().add(orientation_label);
        hb3.getChildren().add(rb4);
        hb3.getChildren().add(rb5);

        HBox hb4 = new HBox();
        hb4.setSpacing(10);
        Label left_reading_label = new Label("Leftmost reading of the main dial");
        TextField left_reading_text = new TextField ();
        left_reading_text.setText("0");
        hb4.getChildren().add(left_reading_label);
        hb4.getChildren().add(left_reading_text);

        HBox hb5 = new HBox();
        hb5.setSpacing(10);
        Label right_reading_label = new Label("Rightmost reading of the main dial");
        TextField right_reading_text = new TextField ();
        right_reading_text.setText("0");
        hb5.getChildren().add(right_reading_label);
        hb5.getChildren().add(right_reading_text);

        final ToggleGroup tgroup3 = new ToggleGroup();
        HBox hb6 = new HBox();
        hb6.setSpacing(10);
        Label scale_label = new Label("Main dial scale:");
        RadioButton rb6 = new RadioButton("Linear");
        rb6.setToggleGroup(tgroup3);
        rb6.setSelected(true);
        RadioButton rb7 = new RadioButton("Log");
        rb7.setToggleGroup(tgroup3);
        hb6.getChildren().add(scale_label);
        hb6.getChildren().add(rb6);
        hb6.getChildren().add(rb7);

//        HBox hb10 = new HBox();
//        hb10.setSpacing(10);
//        Label picture_time_interval = new Label("Time interval between pictures (in second)");
//        TextField picture_time_interval_text = new TextField ();
//        picture_time_interval_text.setText("60");
//        hb10.getChildren().add(picture_time_interval);
//        hb10.getChildren().add(picture_time_interval_text);

        HBox hb7 = new HBox();
        hb7.setSpacing(10);
        Label log_filename = new Label("Name of the log file");
        TextField log_filename_text = new TextField ();
        log_filename_text.setText("meter_readings.txt");
        hb7.getChildren().add(log_filename);
        hb7.getChildren().add(log_filename_text);

        HBox hb8 = new HBox();
        Label xml_created_label = new Label("");
        xml_created_label.setFont(Font.font("Arial", FontWeight.BOLD, 20));
        xml_created_label.setPrefHeight(50);
        xml_created_label.setPrefWidth(600);
        hb8.getChildren().add(xml_created_label);

        HBox hb9 = new HBox();
        hb9.setSpacing(20);
        Button create_xml = new Button("Create XML");
        create_xml.setPrefWidth(120);
        create_xml.setPrefHeight(30);
        Button done = new Button("Done");
        done.setPrefWidth(120);
        done.setPrefHeight(30);
        hb9.getChildren().add(create_xml);
        hb9.getChildren().add(done);

        VBox vb = new VBox();
        vb.setSpacing(20);
        vb.setPadding(new Insets(20, 50, 50, 50));
        vb.getChildren().add(title_5);
        vb.getChildren().add(hb);
        vb.getChildren().add(hb1);
        vb.getChildren().add(hb2);
        vb.getChildren().add(hb3);
        vb.getChildren().add(hb4);
        vb.getChildren().add(hb5);
        vb.getChildren().add(hb6);
//        vb.getChildren().add(hb10);
        vb.getChildren().add(hb7);
        vb.getChildren().add(hb8);
        vb.getChildren().add(hb9);
        Scene create_xml_scene = new Scene(vb, 800, 600);

        // add a change listener
        tgroup1.selectedToggleProperty().addListener(new ChangeListener<Toggle>() {
            public void changed(ObservableValue<? extends Toggle> ob,
                                Toggle o, Toggle n) {
                RadioButton rb = (RadioButton)tgroup1.getSelectedToggle();
                if (rb != null) {
                    String s = rb.getText();
                    if (s.equals("Circular Dial Only")) type = 1;
                    else if (s.equals("Main Dial Only")) type = 2;
                    else type = 3;

                }
            }
        });
        tgroup2.selectedToggleProperty().addListener(new ChangeListener<Toggle>() {
            public void changed(ObservableValue<? extends Toggle> ob,
                                Toggle o, Toggle n) {
                RadioButton rb = (RadioButton)tgroup2.getSelectedToggle();
                if (rb != null) {
                    String s = rb.getText();
                    if (s.equals("Clockwise")) orien = 1;
                    else if (s.equals("Counter-clockwise")) orien = 2;
                }
            }
        });
        tgroup3.selectedToggleProperty().addListener(new ChangeListener<Toggle>() {
            public void changed(ObservableValue<? extends Toggle> ob,
                                Toggle o, Toggle n) {
                RadioButton rb = (RadioButton)tgroup3.getSelectedToggle();
                if (rb != null) {
                    String s = rb.getText();
                    if (s.equals("Linear")) bottom_dial_type = 1;
                    else if (s.equals("Log")) bottom_dial_type = 2;
                }
            }
        });
        done.setOnAction(event -> {
            stage.close();
        });
        create_xml.setOnAction(event -> {
            angle = Float.parseFloat(base_angle_text.getText());
            num_dials = Integer.parseInt(num_dials_text.getText());
            left = Integer.parseInt(left_reading_text.getText());
            right = Integer.parseInt(right_reading_text.getText());
            filename_tosave = log_filename_text.getText();
//            time_interval = Integer.parseInt(picture_time_interval_text.getText());
            generateXML();
            xml_created_label.setText("XML file is created at \"XML/meter_property.xml\"");
        });

        // next/continue buttons
        continue_1.setOnAction(event -> {
            stage.setScene(modify_image_scene);
        });
        continue_3.setOnAction(event -> {
            FLAG = 0;
            count = 0;
            stage.setScene(get_coord_scene);
        });
        continue_4.setOnAction(event -> {
            base_angle_text.setText(getBaseAngle(path_original));
            num_dials_text.setText(Integer.toString(num_dials));
            stage.setScene(create_xml_scene);
        });
        skip.setOnAction(event -> {
            base_angle_text.setText(getBaseAngle(path_original));
            num_dials_text.setText(Integer.toString(num_dials));
            stage.setScene(create_xml_scene);
        });
        stage.setScene(scene1);
        stage.show();
    }

    private void openFile(File file) throws MalformedURLException {
        imagePath = file.toURI().toURL().toExternalForm();
        image = new Image(imagePath, WIDTH, HEIGHT, true, true);
        imgs[0]= image;
        imageView_original.setImage(image);
        imageView_edit.setImage(image);
        imageView_coord.setImage(image);
    }

    private void saveFileAutomatic(String fileNameToSave, Pane pane) {
        final WritableImage SNAPSHOT = pane.snapshot(new SnapshotParameters(), null);
        final File          FILE     = new File(fileNameToSave);
        try {
            ImageIO.write(SwingFXUtils.fromFXImage(SNAPSHOT, null), "png", FILE);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    private String saveFile(File file, Pane pane) throws MalformedURLException {
        String fileNameToSave = file.getAbsolutePath() + ".jpeg";
        final WritableImage SNAPSHOT = pane.snapshot(new SnapshotParameters(), null);
        final File          FILE     = new File(fileNameToSave);
        try {
            ImageIO.write(SwingFXUtils.fromFXImage(SNAPSHOT, null), "png", FILE);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return fileNameToSave;
    }

    public void generateXML() {
        try {
            DocumentBuilderFactory docFactory = DocumentBuilderFactory.newInstance();
            DocumentBuilder docBuilder = docFactory.newDocumentBuilder();

            // root elements
            Document doc = docBuilder.newDocument();
            Element rootElement = doc.createElement("properties");
            doc.appendChild(rootElement);

//            Element image_path = doc.createElement("image_path");
//            image_path.appendChild(doc.createTextNode(path));
//            rootElement.appendChild(image_path);

            Element image_unedited = doc.createElement("image_unedited");
            image_unedited.appendChild(doc.createTextNode(path_original_relative));
            rootElement.appendChild(image_unedited);

            Element meter_type = doc.createElement("meter_type");
            meter_type.appendChild(doc.createTextNode(Integer.toString(type)));
            rootElement.appendChild(meter_type);

            Element base_angle = doc.createElement("base_angle");
            base_angle.appendChild(doc.createTextNode(Float.toString(angle)));
            rootElement.appendChild(base_angle);

            Element number_of_dial = doc.createElement("number_of_dial");
            number_of_dial.appendChild(doc.createTextNode(Integer.toString(num_dials)));
            rootElement.appendChild(number_of_dial);

            Element orientation = doc.createElement("orientation");
            orientation.appendChild(doc.createTextNode(Integer.toString(orien)));
            rootElement.appendChild(orientation);

            Element coordinates = doc.createElement("coordinates");
            rootElement.appendChild(coordinates);

            Element upper_left_x = doc.createElement("upper_left_x");
            upper_left_x.appendChild(doc.createTextNode(Float.toString(ulx)));
            coordinates.appendChild(upper_left_x);

            Element upper_left_y = doc.createElement("upper_left_y");
            upper_left_y.appendChild(doc.createTextNode(Float.toString(uly)));
            coordinates.appendChild(upper_left_y);

            Element bottom_left_x = doc.createElement("bottom_left_x");
            bottom_left_x.appendChild(doc.createTextNode(Float.toString(blx)));
            coordinates.appendChild(bottom_left_x);

            Element bottom_left_y = doc.createElement("bottom_left_y");
            bottom_left_y.appendChild(doc.createTextNode(Float.toString(bly)));
            coordinates.appendChild(bottom_left_y);

            Element upper_right_x = doc.createElement("upper_right_x");
            upper_right_x.appendChild(doc.createTextNode(Float.toString(urx)));
            coordinates.appendChild(upper_right_x);

            Element upper_right_y = doc.createElement("upper_right_y");
            upper_right_y.appendChild(doc.createTextNode(Float.toString(ury)));
            coordinates.appendChild(upper_right_y);

            Element bottom_right_x = doc.createElement("bottom_right_x");
            bottom_right_x.appendChild(doc.createTextNode(Float.toString(brx)));
            coordinates.appendChild(bottom_right_x);

            Element bottom_right_y = doc.createElement("bottom_right_y");
            bottom_right_y.appendChild(doc.createTextNode(Float.toString(bry)));
            coordinates.appendChild(bottom_right_y);

            Element boundary_reading = doc.createElement("boundary_reading");
            rootElement.appendChild(boundary_reading);

            Element left_reading = doc.createElement("left_reading");
            left_reading.appendChild(doc.createTextNode(Integer.toString(left)));
            boundary_reading.appendChild(left_reading);

            Element right_reading = doc.createElement("right_reading");
            right_reading.appendChild(doc.createTextNode(Integer.toString(right)));
            boundary_reading.appendChild(right_reading);

            Element log_or_linear = doc.createElement("log_or_linear");
            log_or_linear.appendChild(doc.createTextNode(Integer.toString(bottom_dial_type)));
            rootElement.appendChild(log_or_linear);

//            Element time_interval_between_pictures = doc.createElement("time_interval_between_pictures");
//            time_interval_between_pictures.appendChild(doc.createTextNode(Integer.toString(time_interval)));
//            rootElement.appendChild(time_interval_between_pictures);

            Element filename_to_save = doc.createElement("filename_to_save");
            filename_to_save.appendChild(doc.createTextNode(filename_tosave));
            rootElement.appendChild(filename_to_save);

            // write the content into xml file
            TransformerFactory transformerFactory = TransformerFactory.newInstance();
            Transformer transformer = transformerFactory.newTransformer();
            transformer.setOutputProperty(OutputKeys.ENCODING, "UTF-8");
            transformer.setOutputProperty(OutputKeys.INDENT, "yes");
            DOMSource source = new DOMSource(doc);
            String fileName = "XML/meter_property.xml";
            StreamResult result = new StreamResult(new File(fileName));
            transformer.transform(source, result);
        } catch (ParserConfigurationException pce) {
            pce.printStackTrace();
        } catch (TransformerException tfe) {
            tfe.printStackTrace();
        }
    }

    private String getBaseAngle(String path) {

        // run python script
        ProcessBuilder pb = new ProcessBuilder("/usr/local/bin/python3", "find_base_angle.py", path);
        File log = new File("log.txt");
        pb.redirectErrorStream(true);
        pb.redirectOutput(ProcessBuilder.Redirect.appendTo(log));
        Process p = null;
        try {
            p = pb.start();
            assert pb.redirectInput() == ProcessBuilder.Redirect.PIPE;
            assert pb.redirectOutput().file() == log;
            assert p.getInputStream().read() == -1;
        } catch (IOException e) {
            e.printStackTrace();
        }

        // read from log
        String s_base_angle = "";
        try {
            FileReader fr = new FileReader(log);
            BufferedReader br = new BufferedReader(fr);
            while (true) {
                s_base_angle = br.readLine();
                if (s_base_angle != null) break;
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return s_base_angle;
    }

}