package TAREFAS;
import java.awt.AWTException;
import java.awt.Robot;
import java.awt.event.KeyEvent;

public class AlterarNomeDoCurso {
    private static Robot robot;                     
    static {
        try {
            robot = new Robot();
        } catch (AWTException e) {
            throw new RuntimeException(e);
        }
    }

    public static void executarBotCurso() {
        timeSleep(5000);
        for (int loop = 0; loop < 200; loop++) {
            pressKey(KeyEvent.VK_DOWN);
            timeSleep(5000);
            pressKey(KeyEvent.VK_ENTER);    
            timeSleep(5000);
            hotkey(KeyEvent.VK_SHIFT, KeyEvent.VK_TAB);
            timeSleep(1000);  
            pressKey(KeyEvent.VK_TAB);
            timeSleep(1000);
            pressKey(KeyEvent.VK_TAB);
            timeSleep(1000);
            hotkey(KeyEvent.VK_CONTROL, KeyEvent.VK_V);
            timeSleep(1000);
            for (int i = 0; i < 28; i++) {
                pressKey(KeyEvent.VK_TAB);
            }
            timeSleep(1000);
            for (int i = 0; i < 2; i++) {
                pressKey(KeyEvent.VK_ENTER);
            }
        }
    }

    private static void timeSleep(int milliseconds) {
        try {
            Thread.sleep(milliseconds);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
    }

    private static void pressKey(int keyCode) {
        robot.keyPress(keyCode);
        robot.keyRelease(keyCode);
    }

    private static void hotkey(int key1, int key2) {
        robot.keyPress(key1);
        robot.keyPress(key2);
        robot.keyRelease(key2);
        robot.keyRelease(key1);
    }
    public static void main(String[] args) {
        executarBotCurso();
    }
}